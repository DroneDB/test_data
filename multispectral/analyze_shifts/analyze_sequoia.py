import struct, re

def extract_sequoia_data(path):
    with open(path, 'rb') as f:
        data = f.read()
    endian = '<'
    ifd_offset = struct.unpack_from(endian + 'I', data, 4)[0]
    num = struct.unpack_from(endian + 'H', data, ifd_offset)[0]
    result = {}
    for i in range(num):
        off = ifd_offset + 2 + i*12
        tag = struct.unpack_from(endian + 'H', data, off)[0]
        if tag == 0x8769:
            exif_off = struct.unpack_from(endian + 'I', data, off+8)[0]
            en = struct.unpack_from(endian + 'H', data, exif_off)[0]
            for j in range(en):
                eoff = exif_off + 2 + j*12
                etag, etyp, ecount = struct.unpack_from(endian + 'HHI', data, eoff)
                eval_off = struct.unpack_from(endian + 'I', data, eoff+8)[0]
                if etyp == 5 and ecount == 1:
                    n, d = struct.unpack_from(endian + 'II', data, eval_off)
                    val = n/d if d else 0
                elif etyp == 3 and ecount == 1:
                    val = struct.unpack_from(endian + 'H', data, eoff+8)[0]
                else:
                    continue
                if etag == 0x920A: result['FocalLength'] = val
                elif etag == 0xA20E: result['FPXRes'] = val
                elif etag == 0xA20F: result['FPYRes'] = val
                elif etag == 0xA210: result['FPResUnit'] = val
                elif etag == 0xA405: result['FL35mm'] = val
    xmp_start = data.find(b'<x:xmpmeta')
    xmp_end = data.find(b'</x:xmpmeta>')
    if xmp_start >= 0 and xmp_end >= 0:
        xmp = data[xmp_start:xmp_end+12].decode('utf-8','replace')
        for tag in ['RigName','RigCameraIndex','PrincipalPoint','ModelType','RigRelatives']:
            m = re.search(r'Camera:' + tag + r'="([^"]+)"', xmp)
            if m:
                result['XMP:'+tag] = m.group(1)
        for tag in ['BandName','CentralWavelength']:
            m = re.search(r'<Camera:' + tag + r'>.*?<rdf:li>([^<]+)</rdf:li>', xmp, re.DOTALL)
            if m:
                result['XMP:'+tag] = m.group(1)
    return result

files = [
    ('GRE', '/mnt/d/DATA/repos/test_data/multispectral/parrot_sequoia/IMG_180822_135805_0467_GRE.TIF'),
    ('RED', '/mnt/d/DATA/repos/test_data/multispectral/parrot_sequoia/IMG_180822_135805_0467_RED.TIF'),
    ('REG', '/mnt/d/DATA/repos/test_data/multispectral/parrot_sequoia/IMG_180822_135805_0467_REG.TIF'),
    ('NIR', '/mnt/d/DATA/repos/test_data/multispectral/parrot_sequoia/IMG_180822_135805_0467_NIR.TIF'),
]

ref_cx, ref_cy = None, None
for name, path in files:
    d = extract_sequoia_data(path)
    pp = d.get('XMP:PrincipalPoint','')
    cx, cy = (float(x) for x in pp.split(',')) if pp else (0, 0)
    if ref_cx is None:
        ref_cx, ref_cy = cx, cy
    fpx = d.get('FPXRes', 0)
    pixel_pitch = 1.0 / fpx if fpx else 0
    dx = (cx - ref_cx) / pixel_pitch if pixel_pitch else 0
    dy = (cy - ref_cy) / pixel_pitch if pixel_pitch else 0
    ri = d.get('XMP:RigCameraIndex','?')
    bn = d.get('XMP:BandName','?')
    wl = d.get('XMP:CentralWavelength','?')
    mt = d.get('XMP:ModelType','?')
    rr = d.get('XMP:RigRelatives','(none)')
    fl = d.get('FocalLength', 0)
    fl35 = d.get('FL35mm', 0)
    print(f"=== {name} (Band: {bn}, {wl} nm, RigIdx: {ri}) ===")
    print(f"  PP: ({cx:.6f}, {cy:.6f}) mm")
    print(f"  FocalLength: {fl:.4f} mm, FL35: {fl35}, FPXRes: {fpx:.4f} px/mm (unit=mm)")
    print(f"  PixelPitch: {pixel_pitch:.6f} mm = {pixel_pitch*1000:.3f} um")
    print(f"  ModelType: {mt}")
    print(f"  RigRelatives: {rr}")
    print(f"  Shift vs ref: ({dx:.1f}, {dy:.1f}) px")
    print()
