#!/usr/bin/env python3
"""Extract and analyze XMP/EXIF metadata from Sentera 6X files."""
import struct, os, re

BASE = "/mnt/d/DATA/repos/test_data/multispectral/sentera_6x"

def extract_xmp(filepath):
    with open(filepath, "rb") as f:
        data = f.read()
    start = data.find(b"<x:xmpmeta")
    if start < 0:
        start = data.find(b"<?xpacket begin")
    if start < 0:
        return None
    end = data.find(b"</x:xmpmeta>", start)
    if end < 0:
        end = data.find(b"<?xpacket end", start)
    if end < 0:
        return None
    end = data.find(b">", end) + 1
    return data[start:end].decode("utf-8", errors="replace")

def find_exif_info(filepath):
    with open(filepath, "rb") as f:
        data = f.read()
    results = {}
    if data[:2] == b'\xff\xd8':
        app1_start = data.find(b'Exif\x00\x00')
        if app1_start < 0:
            return results
        data = data[app1_start+6:]
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
        num = struct.unpack_from(endian + 'H', data, offset)[0]
        if num > 500:
            return tags
        for i in range(num):
            eo = offset + 2 + i * 12
            if eo + 12 > len(data):
                break
            tag, typ, count, val_off = struct.unpack_from(endian + 'HHII', data, eo)
            tags[tag] = (typ, count, val_off, eo)
        return tags
    def read_rational(offset):
        num = struct.unpack_from(endian + 'I', data, offset)[0]
        den = struct.unpack_from(endian + 'I', data, offset + 4)[0]
        return num / den if den else 0
    def read_string(offset, count):
        return data[offset:offset+count].decode('ascii', errors='replace').strip('\x00 ')
    main_tags = read_ifd(ifd_offset)
    for tag_id, name in [(271, 'Make'), (272, 'Model')]:
        if tag_id in main_tags:
            typ, count, off, eo = main_tags[tag_id]
            if count <= 4:
                results[name] = data[eo+8:eo+8+count].decode('ascii', errors='replace').strip('\x00')
            else:
                results[name] = read_string(off, count)
    if 34665 in main_tags:
        _, _, exif_off, _ = main_tags[34665]
        exif_tags = read_ifd(exif_off)
        for tag_id, name in [(37386, 'FocalLength'), (41486, 'FocalPlaneXRes'), (41487, 'FocalPlaneYRes')]:
            if tag_id in exif_tags:
                _, _, off, _ = exif_tags[tag_id]
                results[name] = read_rational(off)
        if 41488 in exif_tags:
            _, _, val, _ = exif_tags[41488]
            units = {1: 'none', 2: 'inch', 3: 'cm', 4: 'mm', 5: 'um'}
            results['FocalPlaneResUnit'] = units.get(val & 0xFFFF, f'unknown({val})')
        if 42037 in exif_tags:
            _, _, val, _ = exif_tags[42037]
            results['FocalLength35mm'] = val & 0xFFFF
    # Try secondary IFD
    next_off_pos = ifd_offset + 2 + len(main_tags) * 12
    if next_off_pos + 4 <= len(data):
        next_ifd = struct.unpack_from(endian + 'I', data, next_off_pos)[0]
        if 0 < next_ifd < len(data) - 2:
            next_tags = read_ifd(next_ifd)
            if 34665 in next_tags and 'FocalPlaneXRes' not in results:
                _, _, exif_off, _ = next_tags[34665]
                exif_tags = read_ifd(exif_off)
                for tag_id, name in [(37386, 'FocalLength'), (41486, 'FocalPlaneXRes'), (41487, 'FocalPlaneYRes')]:
                    if tag_id in exif_tags:
                        _, _, off, _ = exif_tags[tag_id]
                        results[name] = read_rational(off)
                if 41488 in exif_tags:
                    _, _, val, _ = exif_tags[41488]
                    units = {1: 'none', 2: 'inch', 3: 'cm', 4: 'mm', 5: 'um'}
                    results['FocalPlaneResUnit'] = units.get(val & 0xFFFF, f'unknown({val})')
                if 42037 in exif_tags:
                    _, _, val, _ = exif_tags[42037]
                    results['FocalLength35mm'] = val & 0xFFFF
    return results

files = [
    ("IMG_0013.jpg", "RGB"),
    ("IMG_0013_475_30.tif", "Blue 475nm"),
    ("IMG_0013_550_20.tif", "Green 550nm"),
    ("IMG_0013_670_30.tif", "Red 670nm"),
    ("IMG_0013_715_10.tif", "RedEdge 715nm"),
    ("IMG_0013_840_20.tif", "NIR 840nm"),
]

print("=" * 80)
print("Sentera 6X Analysis — Capture 1 (IMG_0013)")
print("=" * 80)

for fname, label in files:
    fpath = os.path.join(BASE, fname)
    print(f"\n{'='*60}")
    print(f"=== {label} ({fname}) ===")
    print(f"{'='*60}")
    xmp = extract_xmp(fpath)
    if xmp:
        print(f"XMP length: {len(xmp)} chars")
        namespaces = re.findall(r'xmlns:(\w+)="([^"]+)"', xmp)
        print("\nNamespaces:")
        for ns, uri in namespaces:
            print(f"  {ns}: {uri}")
        camera_attr = re.findall(r'Camera:(\w+)="([^"]*)"', xmp)
        if camera_attr:
            print("\nCamera (Pix4D) attribute tags:")
            for tag, val in camera_attr:
                print(f"  Camera:{tag} = {val}")
        camera_elem = re.findall(r'<Camera:(\w+)>(.*?)</Camera:\w+>', xmp, re.DOTALL)
        if camera_elem:
            print("\nCamera (Pix4D) element tags:")
            for tag, val in camera_elem:
                print(f"  Camera:{tag} = {val.strip()[:200]}")
        dji_attr = re.findall(r'drone-dji:(\w+)="([^"]*)"', xmp)
        if dji_attr:
            print("\nDJI tags (unexpected):")
            for tag, val in dji_attr:
                print(f"  drone-dji:{tag} = {val}")
        # Search all other namespaced attributes
        all_attrs = re.findall(r'(\w[\w-]*):(\w+)="([^"]*)"', xmp)
        known_ns = {'xmlns', 'rdf', 'x', 'tiff', 'exif', 'xmp', 'xmpMM', 'dc', 'crs',
                     'GPano', 'Camera', 'drone', 'photoshop', 'stEvt'}
        other = [(ns, tag, val) for ns, tag, val in all_attrs if ns not in known_ns]
        if other:
            print("\nOther namespace tags:")
            for ns, tag, val in other[:40]:
                print(f"  {ns}:{tag} = {val}")
        # Key wildcard searches
        for key in ["PrincipalPoint", "FocalLength", "RigCameraIndex", "BandName",
                     "CentralWavelength", "ModelType", "CaptureUUID", "CaptureId",
                     "RigName", "RigRelatives", "RelativeOpticalCenter",
                     "CalibratedFocalLength", "SensorIndex", "Capture", "Band"]:
            matches_e = re.findall(rf'<[\w:-]*{key}[\w]*>(.*?)</[\w:-]*{key}[\w]*>', xmp, re.IGNORECASE | re.DOTALL)
            if matches_e:
                for m in matches_e:
                    print(f"  ** {key} elem: {m.strip()[:200]}")
        # Print raw XMP for first MS band
        if fname == "IMG_0013_475_30.tif":
            print(f"\n--- RAW XMP ---")
            print(xmp[:4000])
            print("--- END RAW ---")
    else:
        print("  NO XMP FOUND")
    exif = find_exif_info(fpath)
    if exif:
        print(f"\nEXIF: {exif}")
#!/usr/bin/env python3
"""Extract and analyze XMP/EXIF metadata from Sentera 6X files."""
import struct, os, re

BASE = "/mnt/d/DATA/repos/test_data/multispectral/sentera_6x"

def extract_xmp(filepath):
    with open(filepath, "rb") as f:
        data = f.read()
    start = data.find(b"<x:xmpmeta")
    if start < 0:
        start = data.find(b"<?xpacket begin")
    if start < 0:
        return None
    end = data.find(b"</x:xmpmeta>", start)
    if end < 0:
        end = data.find(b"<?xpacket end", start)
    if end < 0:
        return None
    end = data.find(b">", end) + 1
    return data[start:end].decode("utf-8", errors="replace")

def find_exif_info(filepath):
    with open(filepath, "rb") as f:
        data = f.read()
    results = {}

    # Handle JPEG vs TIFF
    if data[:2] in (b'\xff\xd8',):
        # JPEG
        app1_start = data.find(b'Exif\x00\x00')
        if app1_start < 0:
            return results
        data = data[app1_start+6:]

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
        num = struct.unpack_from(endian + 'H', data, offset)[0]
        if num > 500:
            return tags
        for i in range(num):
            eo = offset + 2 + i * 12
            if eo + 12 > len(data):
                break
            tag, typ, count, val_off = struct.unpack_from(endian + 'HHII', data, eo)
            tags[tag] = (typ, count, val_off, eo)
        return tags

    def read_rational(offset):
        num = struct.unpack_from(endian + 'I', data, offset)[0]
        den = struct.unpack_from(endian + 'I', data, offset + 4)[0]
        return num / den if den else 0

    def read_string(offset, count):
        return data[offset:offset+count].decode('ascii', errors='replace').strip('\x00 ')

    # Try all IFDs (some cameras put EXIF in a later IFD)
    current_ifd = ifd_offset
    ifd_count = 0
    while current_ifd > 0 and current_ifd < len(data) - 2 and ifd_count < 5:
        ifd_count += 1
        main_tags = read_ifd(current_ifd)

        # Make (271), Model (272)
        for tag_id, name in [(271, 'Make'), (272, 'Model')]:
            if tag_id in main_tags and name not in results:
                typ, count, off, eo = main_tags[tag_id]
                if count <= 4:
                    results[name] = data[eo+8:eo+8+count].decode('ascii', errors='replace').strip('\x00')
                else:
                    results[name] = read_string(off, count)

        # ExifIFD (34665)
        if 34665 in main_tags:
            _, _, exif_off, _ = main_tags[34665]
            exif_tags = read_ifd(exif_off)
            for tag_id, name in [
                (37386, 'FocalLength'),
                (41486, 'FocalPlaneXRes'),
                (41487, 'FocalPlaneYRes'),
            ]:
                if tag_id in exif_tags and name not in results:
                    _, _, off, _ = exif_tags[tag_id]
                    results[name] = read_rational(off)
            if 41488 in exif_tags and 'FocalPlaneResUnit' not in results:
                _, _, val, _ = exif_tags[41488]
                units = {1: 'none', 2: 'inch', 3: 'cm', 4: 'mm', 5: 'um'}
                results['FocalPlaneResUnit'] = units.get(val & 0xFFFF, f'unknown({val})')
            if 42037 in exif_tags and 'FocalLength35mm' not in results:
                _, _, val, _ = exif_tags[42037]
                results['FocalLength35mm'] = val & 0xFFFF

        # Next IFD
        next_pos = current_ifd + 2 + len(main_tags) * 12
        if next_pos + 4 <= len(data):
            current_ifd = struct.unpack_from(endian + 'I', data, next_pos)[0]
        else:
            break

    return results


# Analyze first capture
files = [
    ("IMG_0013.jpg",        "RGB"),
    ("IMG_0013_475_30.tif", "Blue 475nm"),
    ("IMG_0013_550_20.tif", "Green 550nm"),
    ("IMG_0013_670_30.tif", "Red 670nm"),
    ("IMG_0013_715_10.tif", "RedEdge 715nm"),
    ("IMG_0013_840_20.tif", "NIR 840nm"),
]

print("=" * 80)
print("Sentera 6X Analysis — Capture IMG_0013")
print("=" * 80)

for fname, label in files:
    fpath = os.path.join(BASE, fname)
    print(f"\n{'='*60}")
    print(f"=== {label} ({fname}) ===")
    print(f"{'='*60}")

    xmp = extract_xmp(fpath)
    if xmp:
        print(f"XMP length: {len(xmp)} chars")

        namespaces = re.findall(r'xmlns:(\w+)="([^"]+)"', xmp)
        print("\nNamespaces:")
        for ns, uri in namespaces:
            print(f"  {ns}: {uri}")

        # Camera (Pix4D) tags
        camera_attr = re.findall(r'Camera:(\w+)="([^"]*)"', xmp)
        if camera_attr:
            print("\nCamera (Pix4D) attribute tags:")
            for tag, val in camera_attr:
                print(f"  Camera:{tag} = {val}")

        camera_elem = re.findall(r'<Camera:(\w+)>(.*?)</Camera:\w+>', xmp, re.DOTALL)
        if camera_elem:
            print("\nCamera (Pix4D) element tags:")
            for tag, val in camera_elem:
                print(f"  Camera:{tag} = {val.strip()[:200]}")

        # DJI tags (unlikely but check)
        dji_attr = re.findall(r'drone-dji:(\w+)="([^"]*)"', xmp)
        if dji_attr:
            print("\nDJI tags:")
            for tag, val in dji_attr:
                print(f"  drone-dji:{tag} = {val}")

        # Sentera-specific tags
        sentera_attr = re.findall(r'[Ss]entera:(\w+)="([^"]*)"', xmp)
        if sentera_attr:
            print("\nSentera tags:")
            for tag, val in sentera_attr:
                print(f"  Sentera:{tag} = {val}")

        # Any other interesting tags
        all_attr = re.findall(r'(\w+:\w+)="([^"]*)"', xmp)
        known_ns = {'xmlns', 'rdf', 'x', 'tiff', 'exif', 'xmp', 'xmpMM', 'dc', 'crs', 'photoshop', 'Camera', 'drone-dji'}
        for full_tag, val in all_attr:
            ns = full_tag.split(':')[0]
            if ns not in known_ns and len(val) < 200:
                print(f"  OTHER: {full_tag} = {val}")

        # Search for any PrincipalPoint, FocalLength etc
        for key in ["PrincipalPoint", "OpticalCenter", "FocalLength", "RigRelatives",
                     "RigCameraIndex", "BandName", "CentralWavelength", "ModelType",
                     "CaptureUUID", "CaptureId", "SensorIndex", "Alignment",
                     "CalibrationPicture", "CalibrationBoard"]:
            matches = re.findall(rf'[\w:-]*{key}[\w]*="([^"]*)"', xmp, re.IGNORECASE)
            if matches:
                print(f"  ** {key}: {matches}")
            matches2 = re.findall(rf'<[\w:-]*{key}[\w]*>(.*?)</[\w:-]*{key}[\w]*>', xmp, re.IGNORECASE | re.DOTALL)
            if matches2:
                for m in matches2:
                    print(f"  ** {key} element: {m.strip()[:200]}")
    else:
        print("  NO XMP FOUND")

    exif = find_exif_info(fpath)
    if exif:
        print(f"\nEXIF: {exif}")
    else:
        print("\nEXIF: none found")
