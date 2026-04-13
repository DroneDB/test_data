#!/usr/bin/env python3
"""Calculate band alignment shifts for DJI P4 Multispectral (FC6360)."""

# Data extracted from XMP analysis
# All bands: 1600x1300, UInt16, FL=5.74mm, CalibratedFL=1913.333374 px
# Model: FC6360 (P4 Multispectral), RigName: FC6360
# Namespace: Pix4D Camera + drone-dji (same as M3M)

BANDS = [
    # (file, name, wavelength, rig_idx, pp_x_mm, pp_y_mm, roc_x, roc_y)
    ("DJI_0021.TIF", "Blue",    450, 1, 2.411205, 1.991532, -5.96875, -6.12500),
    ("DJI_0022.TIF", "Green",   560, 2, 2.411355, 1.990968, -1.65625, -9.25000),
    ("DJI_0023.TIF", "Red",     650, 3, 2.414835, 1.991682,  1.68750,  0.00000),
    ("DJI_0024.TIF", "RedEdge", 730, 4, 2.410527, 1.993731, -2.03125,  2.71875),
    ("DJI_0025.TIF", "NIR",     840, 5, 2.410260, 1.992228,  0.00000,  0.00000),
]

FL_MM = 5.74
CFL_PX = 1913.333374
WIDTH = 1600
HEIGHT = 1300

pixel_pitch = FL_MM / CFL_PX
sensor_w = WIDTH * pixel_pitch
sensor_h = HEIGHT * pixel_pitch

print("=" * 80)
print("DJI P4 Multispectral (FC6360) — Shift Analysis")
print("=" * 80)
print(f"Resolution: {WIDTH} x {HEIGHT} px, UInt16")
print(f"FocalLength: {FL_MM} mm")
print(f"CalibratedFocalLength: {CFL_PX} px")
print(f"Pixel pitch: {pixel_pitch:.6f} mm = {pixel_pitch*1000:.3f} µm")
print(f"Sensor dimensions: {sensor_w:.3f} x {sensor_h:.3f} mm")
print(f"EXIF Make/Model: DJI / FC6360")
print(f"FocalPlaneResolution: NOT PRESENT")
print(f"FocalLength35mm: NOT PRESENT")
print(f"Lens model: perspective (Brown 5-param)")
print(f"RigCameraIndex: 1-5 (no index 0)")
print(f"CaptureUUID: identical on all bands")

# Reference = Blue (index 0, first band)
ref = BANDS[0]

print(f"\n{'='*80}")
print(f"Shifts from PrincipalPoint (ref = {ref[1]}, RigIdx={ref[3]})")
print(f"{'='*80}")

for f, name, wl, ri, ppx, ppy, rocx, rocy in BANDS:
    dx_mm = ppx - ref[4]
    dy_mm = ppy - ref[5]
    dx_px = dx_mm / pixel_pitch
    dy_px = dy_mm / pixel_pitch

    print(f"\n{name:8s} ({wl} nm, RigIdx={ri})")
    print(f"  PP: ({ppx:.6f}, {ppy:.6f}) mm")
    print(f"  DJI RelativeOpticalCenter: ({rocx:+.5f}, {rocy:+.5f}) px")
    if name == ref[1]:
        print(f"  Shift: (0, 0) px [REFERENCE]")
    else:
        print(f"  ΔPP: ({dx_mm:+.6f}, {dy_mm:+.6f}) mm")
        print(f"  Shift (from PP): ({dx_px:+.1f}, {dy_px:+.1f}) px")

# Also show shifts using NIR as reference (DJI uses NIR=reference with RelOC=0,0)
nir = BANDS[4]
print(f"\n{'='*80}")
print(f"Shifts from PrincipalPoint (ref = NIR, for DJI RelOC comparison)")
print(f"{'='*80}")
for f, name, wl, ri, ppx, ppy, rocx, rocy in BANDS:
    dx_mm = ppx - nir[4]
    dy_mm = ppy - nir[5]
    dx_px = dx_mm / pixel_pitch
    dy_px = dy_mm / pixel_pitch
    print(f"  {name:8s}: PP shift=({dx_px:+5.1f}, {dy_px:+5.1f}) px  |  DJI RelOC=({rocx:+8.5f}, {rocy:+8.5f}) px")

# Key observation
print(f"\n{'='*80}")
print("KEY OBSERVATIONS")
print(f"{'='*80}")
print(f"1. PP variations are TINY: max ΔPP = {max(abs(b[4]-ref[4]) for b in BANDS):.6f} mm = {max(abs(b[4]-ref[4]) for b in BANDS)/pixel_pitch:.1f} px (X), {max(abs(b[5]-ref[5]) for b in BANDS):.6f} mm = {max(abs(b[5]-ref[5]) for b in BANDS)/pixel_pitch:.1f} px (Y)")
print(f"2. DJI RelativeOpticalCenter shows LARGER shifts (up to {max(abs(b[6]) for b in BANDS):.2f} px X, {max(abs(b[7]) for b in BANDS):.2f} px Y)")
print(f"3. DJI DewarpHMatrix for NIR is IDENTITY matrix → NIR is the reference")
print(f"4. CalibratedHMatrix/DewarpHMatrix contain the real alignment info")
print(f"5. PrincipalPoint differences alone may underestimate the real misalignment")
print(f"6. THIS IS A 6-CAMERA SYSTEM (5 MS + 1 RGB), not multi-camera rig like MicaSense")
print(f"   The FC6360 sensor model name is the same for all bands!")
