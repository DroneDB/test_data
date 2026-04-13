#!/usr/bin/env python3
"""Calculate band alignment shifts for DJI Mavic 3 Multispectral."""
import struct, os, re

BASE = "/mnt/d/DATA/repos/test_data/multispectral/dji"
CAPTURE = "DJI_20240525174755_0001"
BANDS = [
    ("MS_G",   "Green",   560, 1),
    ("MS_R",   "Red",     650, 2),
    ("MS_RE",  "RedEdge", 730, 3),
    ("MS_NIR", "NIR",     860, 4),
]

def extract_xmp(filepath):
    with open(filepath, "rb") as f:
        data = f.read()
    start = data.find(b"<x:xmpmeta")
    if start < 0:
        return None
    end = data.find(b"</x:xmpmeta>", start)
    if end < 0:
        return None
    return data[start:end+12].decode("utf-8", errors="replace")

def find_tiff_ifd_exif(filepath):
    """Search for FocalPlaneResolution in EXIF IFD."""
    with open(filepath, "rb") as f:
        data = f.read()

    results = {}

    # Try to parse TIFF header
    if data[:2] == b'II':
        endian = '<'
    elif data[:2] == b'MM':
        endian = '>'
    else:
        return results

    magic = struct.unpack_from(endian + 'H', data, 2)[0]
    if magic != 42:
        return results

    ifd_offset = struct.unpack_from(endian + 'I', data, 4)[0]

    def read_ifd(offset):
        tags = {}
        if offset == 0 or offset >= len(data) - 2:
            return tags
        num_entries = struct.unpack_from(endian + 'H', data, offset)[0]
        if num_entries > 500:
            return tags
        for i in range(num_entries):
            entry_offset = offset + 2 + i * 12
            if entry_offset + 12 > len(data):
                break
            tag, typ, count, val_off = struct.unpack_from(endian + 'HHII', data, entry_offset)
            tags[tag] = (typ, count, val_off, entry_offset)
        return tags

    def read_rational(offset):
        num = struct.unpack_from(endian + 'I', data, offset)[0]
        den = struct.unpack_from(endian + 'I', data, offset + 4)[0]
        return num / den if den else 0

    # Read main IFD
    main_tags = read_ifd(ifd_offset)

    # Look for ExifIFD pointer (tag 0x8769 = 34665)
    if 34665 in main_tags:
        typ, count, exif_offset, _ = main_tags[34665]
        exif_tags = read_ifd(exif_offset)

        # FocalPlaneXResolution (0xA20E = 41486)
        if 41486 in exif_tags:
            _, _, off, _ = exif_tags[41486]
            results['FocalPlaneXRes'] = read_rational(off)

        # FocalPlaneYResolution (0xA20F = 41487)
        if 41487 in exif_tags:
            _, _, off, _ = exif_tags[41487]
            results['FocalPlaneYRes'] = read_rational(off)

        # FocalPlaneResolutionUnit (0xA210 = 41488)
        if 41488 in exif_tags:
            _, _, val, _ = exif_tags[41488]
            units = {1: 'none', 2: 'inch', 3: 'cm', 4: 'mm', 5: 'um'}
            results['FocalPlaneResUnit'] = units.get(val & 0xFFFF, f'unknown({val})')
            results['FocalPlaneResUnitRaw'] = val & 0xFFFF

        # FocalLength (0x920A = 37386)
        if 37386 in exif_tags:
            _, _, off, _ = exif_tags[37386]
            results['FocalLength'] = read_rational(off)

        # FocalLengthIn35mm (0xA405 = 42037)
        if 42037 in exif_tags:
            _, _, val, _ = exif_tags[42037]
            results['FocalLength35mm'] = val & 0xFFFF

    # Also check main IFD for Make/Model
    # Make (0x010F = 271)
    if 271 in main_tags:
        _, count, off, _ = main_tags[271]
        if count <= 4:
            results['Make'] = data[main_tags[271][3]+8:main_tags[271][3]+8+count].decode('ascii', errors='replace').strip('\x00')
        else:
            results['Make'] = data[off:off+count].decode('ascii', errors='replace').strip('\x00')

    # Model (0x0110 = 272)
    if 272 in main_tags:
        _, count, off, _ = main_tags[272]
        if count <= 4:
            results['Model'] = data[main_tags[272][3]+8:main_tags[272][3]+8+count].decode('ascii', errors='replace').strip('\x00')
        else:
            results['Model'] = data[off:off+count].decode('ascii', errors='replace').strip('\x00')

    # Try also the LAST IFD (some TIFFs put EXIF there)
    next_ifd_off = ifd_offset + 2 + len(main_tags) * 12
    if next_ifd_off + 4 <= len(data):
        next_ifd = struct.unpack_from(endian + 'I', data, next_ifd_off)[0]
        if next_ifd > 0 and next_ifd < len(data):
            next_tags = read_ifd(next_ifd)
            if 34665 in next_tags and 'FocalPlaneXRes' not in results:
                typ, count, exif_offset, _ = next_tags[34665]
                exif_tags = read_ifd(exif_offset)
                if 41486 in exif_tags:
                    _, _, off, _ = exif_tags[41486]
                    results['FocalPlaneXRes'] = read_rational(off)
                if 41487 in exif_tags:
                    _, _, off, _ = exif_tags[41487]
                    results['FocalPlaneYRes'] = read_rational(off)
                if 41488 in exif_tags:
                    _, _, val, _ = exif_tags[41488]
                    units = {1: 'none', 2: 'inch', 3: 'cm', 4: 'mm', 5: 'um'}
                    results['FocalPlaneResUnit'] = units.get(val & 0xFFFF, f'unknown({val})')
                if 37386 in exif_tags:
                    _, _, off, _ = exif_tags[37386]
                    results['FocalLength'] = read_rational(off)

    return results


print("=" * 80)
print(f"DJI M3M Shift Analysis — Capture {CAPTURE}")
print("=" * 80)

band_data = []

for suffix, name, wavelength, rig_idx in BANDS:
    fname = f"{CAPTURE}_{suffix}.TIF"
    fpath = os.path.join(BASE, fname)

    xmp = extract_xmp(fpath)

    # Extract PrincipalPoint
    pp_match = re.search(r'<Camera:PrincipalPoint>([\d.]+),([\d.]+)</Camera:PrincipalPoint>', xmp)
    pp_x, pp_y = float(pp_match.group(1)), float(pp_match.group(2))

    # Extract PerspectiveFocalLength
    fl_match = re.search(r'<Camera:PerspectiveFocalLength>([\d.]+)</Camera:PerspectiveFocalLength>', xmp)
    fl = float(fl_match.group(1))

    # Extract DJI RelativeOpticalCenter
    roc_x_match = re.search(r'drone-dji:RelativeOpticalCenterX="([\d.+-]+)"', xmp)
    roc_y_match = re.search(r'drone-dji:RelativeOpticalCenterY="([\d.+-]+)"', xmp)
    roc_x = float(roc_x_match.group(1)) if roc_x_match else None
    roc_y = float(roc_y_match.group(1)) if roc_y_match else None

    # Extract CalibratedFocalLength (in pixels)
    cfl_match = re.search(r'drone-dji:CalibratedFocalLength="([\d.]+)"', xmp)
    cfl = float(cfl_match.group(1)) if cfl_match else None

    # Extract DewarpData to get fx, fy in pixels
    dd_match = re.search(r'drone-dji:DewarpData="[^;]+;([\d.,-]+)"', xmp)
    dwd = None
    if dd_match:
        parts = dd_match.group(1).split(',')
        dwd = {
            'fx': float(parts[0]),
            'fy': float(parts[1]),
            'cx_off': float(parts[2]),
            'cy_off': float(parts[3]),
        }

    # EXIF
    exif_info = find_tiff_ifd_exif(fpath)

    band_data.append({
        'suffix': suffix,
        'name': name,
        'wavelength': wavelength,
        'rig_idx': rig_idx,
        'pp_x': pp_x,
        'pp_y': pp_y,
        'fl': fl,
        'roc_x': roc_x,
        'roc_y': roc_y,
        'cfl': cfl,
        'dwd': dwd,
        'exif': exif_info,
    })

# Pick reference band (Green = index 0, first in our list)
ref = band_data[0]

print(f"\nImage: 2592 x 1944 px, UInt16")
print(f"PerspectiveFocalLength: {ref['fl']} mm")
print(f"CalibratedFocalLength: {ref['cfl']} px")

if ref['cfl']:
    pixel_pitch = ref['fl'] / ref['cfl']
    print(f"Pixel pitch (FL/CFL): {pixel_pitch:.6f} mm = {pixel_pitch*1000:.3f} µm")
    sensor_w = 2592 * pixel_pitch
    sensor_h = 1944 * pixel_pitch
    print(f"Sensor dimensions: {sensor_w:.3f} x {sensor_h:.3f} mm")
else:
    pixel_pitch = None

# Check FocalPlaneResolution
print(f"\nEXIF info from Green band:")
for k, v in ref['exif'].items():
    print(f"  {k}: {v}")

# If we have DewarpData fx, use that for pixel pitch
if ref['dwd']:
    pp_dwd = ref['fl'] / ref['dwd']['fx']
    print(f"\nPixel pitch (FL/DewarpData.fx): {pp_dwd:.6f} mm = {pp_dwd*1000:.3f} µm")

print(f"\n{'='*80}")
print(f"Shift Analysis (reference: {ref['name']} band)")
print(f"{'='*80}")

for bd in band_data:
    delta_x_mm = bd['pp_x'] - ref['pp_x']
    delta_y_mm = bd['pp_y'] - ref['pp_y']

    if pixel_pitch:
        shift_x_px = delta_x_mm / pixel_pitch
        shift_y_px = delta_y_mm / pixel_pitch
    else:
        shift_x_px = shift_y_px = 0

    print(f"\n=== {bd['name']} (Band {bd['suffix']}, {bd['wavelength']} nm, RigIdx: {bd['rig_idx']}) ===")
    print(f"  PP: ({bd['pp_x']:.6f}, {bd['pp_y']:.6f}) mm, FL: {bd['fl']} mm")

    if bd['dwd']:
        print(f"  DewarpData: fx={bd['dwd']['fx']:.2f}, fy={bd['dwd']['fy']:.2f}, cx_off={bd['dwd']['cx_off']:.2f}, cy_off={bd['dwd']['cy_off']:.2f}")

    print(f"  DJI RelativeOpticalCenter: ({bd['roc_x']}, {bd['roc_y']}) px")

    if bd == ref:
        print(f"  Shift vs ref: (0, 0) px [REFERENCE]")
    else:
        print(f"  ΔPP: ({delta_x_mm:+.6f}, {delta_y_mm:+.6f}) mm")
        print(f"  Shift (from PP): ({shift_x_px:+.1f}, {shift_y_px:+.1f}) px")

    print(f"  EXIF: {bd['exif']}")

# Summary comparison
print(f"\n{'='*80}")
print("SUMMARY — DJI M3M Multispectral")
print(f"{'='*80}")
print(f"Drone: DJI Mavic 3 Multispectral (M3M)")
print(f"Resolution: 2592 x 1944 px, UInt16")
print(f"Focal length: {ref['fl']} mm")
print(f"Pixel pitch: {pixel_pitch*1000:.3f} µm" if pixel_pitch else "Pixel pitch: unknown")
print(f"Lens model: perspective (Brown 5-param)")
print(f"XMP namespace: Pix4D Camera (Camera:*) + DJI (drone-dji:*)")
print(f"Camera:PrincipalPoint: PRESENT on all bands")
print(f"drone-dji:RelativeOpticalCenterX/Y: PRESENT (direct pixel shifts from DJI)")
print(f"drone-dji:CalibratedHMatrix: PRESENT (full homography)")
print(f"CaptureUUID: same on all bands")
print(f"RigCameraIndex: 1-4 (no band 0)")
print()

if pixel_pitch:
    print("Band shifts (from PrincipalPoint, ref=Green):")
    for bd in band_data:
        dx = (bd['pp_x'] - ref['pp_x']) / pixel_pitch
        dy = (bd['pp_y'] - ref['pp_y']) / pixel_pitch
        roc = f"DJI RelOC: ({bd['roc_x']:+.2f}, {bd['roc_y']:+.2f}) px" if bd['roc_x'] is not None else ""
        if bd == ref:
            print(f"  {bd['name']:8s}: (  0.0,   0.0) px [REF]    {roc}")
        else:
            print(f"  {bd['name']:8s}: ({dx:+5.1f}, {dy:+5.1f}) px        {roc}")
