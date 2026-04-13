#!/usr/bin/env python3
"""Calculate band-to-band pixel shifts for Sentera 6X using PrincipalPoint."""

# Image dimensions (MS bands)
W, H = 1904, 1428

# FocalPlaneResolution from EXIF (px/cm, unit=cm)
FPR = 2898.5504  # px/cm for MS bands
pixel_pitch_cm = 1.0 / FPR  # cm/px
pixel_pitch_um = pixel_pitch_cm * 10000  # μm/px
pixel_pitch_mm = pixel_pitch_cm * 10  # mm/px

print(f"Pixel pitch: {pixel_pitch_um:.4f} μm = {pixel_pitch_mm:.6f} mm")
print(f"Sensor size: {W * pixel_pitch_mm:.3f} x {H * pixel_pitch_mm:.3f} mm")

# PrincipalPoint from XMP (mm) - Camera:PrincipalPoint
bands = {
    "Blue 475":    (0, 3.223, 2.419),
    "Green 550":   (1, 3.301, 2.482),
    "Red 670":     (2, 3.250, 2.492),
    "RedEdge 715": (3, 3.291, 2.464),
    "NIR 840":     (4, 3.364, 2.459),
    "RGB":         (5, 3.110, 2.333),  # Different sensor/lens!
}

# Image center (pixels)
cx, cy = W / 2.0, H / 2.0
print(f"Image center: ({cx}, {cy})")

print("\n=== PrincipalPoint in pixels (PP_mm / pixel_pitch_mm) ===")
pp_px = {}
for name, (idx, ppx_mm, ppy_mm) in bands.items():
    ppx_px = ppx_mm / pixel_pitch_mm
    ppy_px = ppy_mm / pixel_pitch_mm
    offset_x = ppx_px - cx
    offset_y = ppy_px - cy
    pp_px[name] = (ppx_px, ppy_px, offset_x, offset_y)
    print(f"  {name:15s} (idx={idx}): PP=({ppx_px:8.2f}, {ppy_px:8.2f})  "
          f"offset=({offset_x:+7.2f}, {offset_y:+7.2f})")

# Note: RGB has different pixel pitch (8333.3328 px/cm → 1.2μm)
# So we can't directly compare RGB PP with MS PP using same pixel pitch
rgb_fpr = 8333.3328
rgb_pp_mm = pixel_pitch_cm_rgb = 1.0 / rgb_fpr
rgb_pp_um = rgb_pp_mm * 10000  # 1.2 μm
print(f"\nRGB pixel pitch: {rgb_pp_um:.4f} μm (different sensor!)")
# RGB dimensions would be ~5472×3648 for 20MP
# RGB PrincipalPoint in RGB pixels: 3.110 / 0.00012 = 25917, 2.333/0.00012 = 19442

print("\n=== Shifts relative to reference band (Blue 475nm, idx=0) ===")
ref = "Blue 475"
ref_ox, ref_oy = pp_px[ref][2], pp_px[ref][3]
max_shift = 0
for name in ["Green 550", "Red 670", "RedEdge 715", "NIR 840"]:
    ox, oy = pp_px[name][2], pp_px[name][3]
    dx = ox - ref_ox
    dy = oy - ref_oy
    dist = (dx**2 + dy**2) ** 0.5
    max_shift = max(max_shift, dist)
    print(f"  {name:15s} vs {ref}: dx={dx:+7.2f}, dy={dy:+7.2f}  dist={dist:.2f} px")

print(f"\nMax shift: {max_shift:.2f} px")

# Also compute mean PP to use as reference (alternative)
print("\n=== Shifts relative to mean PP (alternative reference) ===")
ms_bands = ["Blue 475", "Green 550", "Red 670", "RedEdge 715", "NIR 840"]
mean_ox = sum(pp_px[b][2] for b in ms_bands) / len(ms_bands)
mean_oy = sum(pp_px[b][2] for b in ms_bands) / len(ms_bands)
# Fix: use offset_y for y
mean_oy = sum(pp_px[b][3] for b in ms_bands) / len(ms_bands)
for name in ms_bands:
    ox, oy = pp_px[name][2], pp_px[name][3]
    dx = ox - mean_ox
    dy = oy - mean_oy
    dist = (dx**2 + dy**2) ** 0.5
    print(f"  {name:15s}: dx={dx:+7.2f}, dy={dy:+7.2f}  dist={dist:.2f} px")

# Sentera:AlignMatrix data (from raw XMP)
# Blue 475: [1.000000, 0.000908, 89.163879, -0.000908, 1.000000, 67.548157, 0, 0, 1]
# This is a 3x3 affine matrix: [a, b, tx; -b, a, ty; 0, 0, 1]
# tx=89.16, ty=67.55 → alignment of Blue to RGB reference
print("\n=== Sentera:AlignMatrix (proprietary, for reference) ===")
print("  Blue 475nm →RGB: tx=89.16, ty=67.55, rot=0.052°")
print("  (This is Sentera's pre-computed alignment TO the RGB camera)")

# Verify KNOWN_SENSORS table entry
print(f"\n=== KNOWN_SENSORS verification ===")
print(f"  Current table: {{'Sentera 6X', 4.8, 3.6}} (WRONG)")
sensor_w = W * pixel_pitch_mm
sensor_h = H * pixel_pitch_mm
print(f"  Actual MS sensor: {sensor_w:.3f} x {sensor_h:.3f} mm")
print(f"  → Should be: {{'Sentera 6X', {sensor_w:.2f}, {sensor_h:.2f}}}")
