#!/usr/bin/env python3
"""Extract and analyze XMP/EXIF metadata from DJI P4 Multispectral files."""
import struct, os, re

BASE = "/mnt/d/DATA/repos/test_data/multispectral/dji"
CAPTURE = "DJI_20240525174755_0001"
BANDS = ["MS_G", "MS_R", "MS_RE", "MS_NIR"]

def extract_xmp(filepath):
    with open(filepath, "rb") as f:
        data = f.read()
    # Find XMP packet
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

def extract_exif_focal(filepath):
    """Try to extract key EXIF tags."""
    with open(filepath, "rb") as f:
        data = f.read()

    results = {}

    # Look for Make/Model in TIFF IFD
    # Search for common strings
    for tag_name in [b"DJI", b"Hasselblad", b"P4 Multispectral", b"Mavic"]:
        pos = data.find(tag_name)
        if pos >= 0:
            end = data.find(b"\x00", pos)
            results[f"found_{tag_name.decode()}"] = data[pos:min(end, pos+50)].decode("utf-8", errors="replace")

    return results

print("=" * 80)
print(f"DJI Multispectral Analysis — Capture {CAPTURE}")
print("=" * 80)

for band_name in BANDS:
    fname = f"{CAPTURE}_{band_name}.TIF"
    fpath = os.path.join(BASE, fname)

    print(f"\n{'='*60}")
    print(f"=== {band_name} ({fname}) ===")
    print(f"{'='*60}")

    xmp = extract_xmp(fpath)
    if xmp:
        print(f"\nXMP length: {len(xmp)} chars")

        # Print interesting parts, not the full dump
        # Look for key namespaces
        namespaces = re.findall(r'xmlns:(\w+)="([^"]+)"', xmp)
        print("\nNamespaces:")
        for ns_prefix, ns_uri in namespaces:
            print(f"  {ns_prefix}: {ns_uri}")

        # Look for Camera namespace (Pix4D)
        camera_tags = re.findall(r'Camera:(\w+)="([^"]*)"', xmp)
        if camera_tags:
            print("\nCamera (Pix4D) tags:")
            for tag, val in camera_tags:
                print(f"  Camera:{tag} = {val}")

        # Look for Camera tags in element form
        camera_elem = re.findall(r'<Camera:(\w+)>(.*?)</Camera:\w+>', xmp, re.DOTALL)
        if camera_elem:
            print("\nCamera (Pix4D) element tags:")
            for tag, val in camera_elem:
                val_clean = val.strip()[:200]
                print(f"  Camera:{tag} = {val_clean}")

        # Look for DJI namespace
        dji_tags = re.findall(r'drone-dji:(\w+)="([^"]*)"', xmp)
        if dji_tags:
            print("\nDJI tags:")
            for tag, val in dji_tags:
                print(f"  drone-dji:{tag} = {val}")

        dji_elem = re.findall(r'<drone-dji:(\w+)>(.*?)</drone-dji:\w+>', xmp, re.DOTALL)
        if dji_elem:
            print("\nDJI element tags:")
            for tag, val in dji_elem:
                val_clean = val.strip()[:200]
                print(f"  drone-dji:{tag} = {val_clean}")

        # Look for any PrincipalPoint or CalibratedOpticalCenter
        for key in ["PrincipalPoint", "CalibratedOpticalCenter", "OpticalCenter",
                     "FocalLength", "PerspectiveFocalLength", "FocalPlane",
                     "RigRelatives", "RigCameraIndex", "BandName", "CentralWavelength",
                     "ModelType", "PerspectiveDistortion", "CaptureUUID", "CaptureId",
                     "SensorIndex", "BandSensorIndex"]:
            matches = re.findall(rf'[\w:-]*{key}[\w]*="([^"]*)"', xmp, re.IGNORECASE)
            if matches:
                print(f"\n  ** {key} matches: {matches}")
            matches2 = re.findall(rf'<[\w:-]*{key}[\w]*>(.*?)</[\w:-]*{key}[\w]*>', xmp, re.IGNORECASE | re.DOTALL)
            if matches2:
                for m in matches2:
                    print(f"  ** {key} element: {m.strip()[:200]}")
    else:
        print("  NO XMP FOUND")

    # EXIF search
    exif_info = extract_exif_focal(fpath)
    if exif_info:
        print(f"\nEXIF string matches: {exif_info}")

# Also check the RGB image for comparison
print(f"\n\n{'='*60}")
print("=== RGB image (_D.JPG) ===")
print(f"{'='*60}")
rgb_path = os.path.join(BASE, f"{CAPTURE}_D.JPG")
xmp = extract_xmp(rgb_path)
if xmp:
    namespaces = re.findall(r'xmlns:(\w+)="([^"]+)"', xmp)
    print("\nNamespaces:")
    for ns_prefix, ns_uri in namespaces:
        print(f"  {ns_prefix}: {ns_uri}")

    dji_tags = re.findall(r'drone-dji:(\w+)="([^"]*)"', xmp)
    if dji_tags:
        print("\nDJI tags:")
        for tag, val in dji_tags:
            print(f"  drone-dji:{tag} = {val}")

    camera_tags = re.findall(r'Camera:(\w+)="([^"]*)"', xmp)
    if camera_tags:
        print("\nCamera (Pix4D) tags:")
        for tag, val in camera_tags:
            print(f"  Camera:{tag} = {val}")
