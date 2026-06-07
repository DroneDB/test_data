# OGC Test Seed Dataset

Reference dataset used by the QGIS smoke-test harness
(`Registry/scripts/qgis-test-setup.ps1` / `.sh`) and by the OGC services
acceptance tests in `Registry.Web.Test/Ogc/`.

The harness uploads everything in this folder to a freshly-created dataset
`qgis-test/ogc-fixture` and prints the resulting WMS/WFS/WMTS/WCS/OGC-API
endpoints so they can be opened in QGIS.

## Suggested layout

```
ogc-seed/
├── README.md           (this file)
├── orthos/
│   ├── rgb.tif         (true-color GeoTIFF, EPSG:32632, ≥3 bands)
│   └── multispec.tif   (5-band multispectral: R, G, B, RedEdge, NIR)
├── vectors/
│   ├── contours.gpkg   (LineString features, ≥1000 rows)
│   └── parcels.fgb     (Polygon features with attributes)
└── annotations/
    └── notes.geojson   (Point features with ad-hoc properties)
```

Any subset of these files works; the harness only checks that the upload
succeeds and that at least one `GeoRaster` plus one `Vector` entry are
indexed.

## Convention for spectral indices

Multispectral rasters are expected to follow the DroneDB band convention:

| Band | Wavelength | Role |
|------|------------|------|
| 1 | Red | R |
| 2 | Green | G |
| 3 | Blue | B |
| 4 | RedEdge | RE |
| 5 | NIR | Near-infrared |

This convention is shared with the multispectral build pipeline and with
the WMS `STYLES=NDVI|NDRE|NDWI|EVI|SAVI` renderer.

## Where to get sample data

If you don't have your own multispectral imagery handy:

- `test_data/multispectral/` in the workspace contains a small Micasense
  RedEdge demo (see the project root `README.md` in this folder).
- `test_data/ortho/` contains a single-flight RGB orthophoto + a contours
  GeoPackage that already satisfy the harness.

Place (or symlink) those files under `orthos/` and `vectors/` to populate
the seed.
