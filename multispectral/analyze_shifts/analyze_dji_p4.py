#!/usr/bin/env python3
"""Extract and analyze XMP/EXIF metadata from DJI P4 Multispectral files."""
import struct, os, re

BASE = "/mnt/d/DATA/repos/test_data/multispectral/dji_p4"

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
    if data[:2] == b'II':
        endian = '<'
    elif data[:2] == b'MM':
        endian = '>'
    else:
        # JPEG - search for TIFF header in APP1
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

    # Make (271), Model (272)
    for tag_id, name in [(271, 'Make'), (272, 'Model')]:
        if tag_id in main_tags:
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

    # Also try last IFD
    next_off_pos = ifd_offset + 2 + len(main_tags) * 12
    if next_off_pos + 4 <= len(data):
        next_ifd = struct.unpack_from(endian + 'I', data, next_off_pos)[0]
        if next_ifd > 0 and next_ifd < len(data) - 2:
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


# Analyze first capture: DJI_0020.JPG (RGB) + DJI_0021-0025.TIF (MS bands)
files_capture1 = [
    ("DJI_0020.JPG", "RGB"),
    ("DJI_0021.TIF", "MS band 1"),
    ("DJI_0022.TIF", "MS band 2"),
    ("DJI_0023.TIF", "MS band 3"),
    ("DJI_0024.TIF", "MS band 4"),
    ("DJI_0025.TIF", "MS band 5"),
]

print("=" * 80)
print("DJI P4 Multispectral Analysis — Capture 1 (DJI_0020-0025)")
print("=" * 80)

for fname, label in files_capture1:
    fpath = os.path.join(BASE, fname)
    print(f"\n{'='*60}")
    print(f"=== {label} ({fname}) ===")
    print(f"{'='*60}")

    xmp = extract_xmp(fpath)
    if xmp:
        print(f"XMP length: {len(xmp)} chars")

        # Namespaces
        namespaces = re.findall(r'xmlns:(\w+)="([^"]+)"', xmp)
        print("\nNamespaces:")
        for ns, uri in namespaces:
            print(f"  {ns}: {uri}")

        # Camera (Pix4D) attribute tags
        camera_attr = re.findall(r'Camera:(\w+)="([^"]*)"', xmp)
        if camera_attr:
            print("\nCamera (Pix4D) attribute tags:")
            for tag, val in camera_attr:
                print(f"  Camera:{tag} = {val}")

        # Camera element tags
        camera_elem = re.findall(r'<Camera:(\w+)>(.*?)</Camera:\w+>', xmp, re.DOTALL)
        if camera_elem:
            print("\nCamera (Pix4D) element tags:")
            for tag, val in camera_elem:
                print(f"  Camera:{tag} = {val.strip()[:200]}")

        # DJI attribute tags
        dji_attr = re.findall(r'drone-dji:(\w+)="([^"]*)"', xmp)
        if dji_attr:
            print("\nDJI tags:")
            for tag, val in dji_attr:
                print(f"  drone-dji:{tag} = {val}")

        # DJI element tags
        dji_elem = re.findall(r'<drone-dji:(\w+)>(.*?)</drone-dji:\w+>', xmp, re.DOTALL)
        if dji_elem:
            print("\nDJI element tags:")
            for tag, val in dji_elem:
                print(f"  drone-dji:{tag} = {val.strip()[:200]}")
    else:
        print("  NO XMP FOUND")

    exif = find_exif_info(fpath)
    if exif:
        print(f"\nEXIF: {exif}")
