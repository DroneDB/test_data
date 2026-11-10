# FLIR radiometric JPEGs: sources and licences

Real FLIR R-JPEGs (radiometric JPEGs with the FFF records in their FLIR APP1 segments) that DroneDB's thermal tests
read. The files are unmodified copies of the published ones. Unlike the rest of this repository, they are not
restricted to DroneDB testing: each one stays under the licence of its source, given here.

| File | Camera | Raw image | Source | Licence |
|------|--------|-----------|--------|---------|
| `SC660/SampleJPG.jpg` | FLIR SC660 | 640 x 480, int16u | ThermImageJ sample image, by Glenn J. Tattersall (https://github.com/gtatters/ThermImageJ); the same file is `IR_2412.jpg` of the Thermimage R package, whose README gives the temperatures of its first column | CC-BY-4.0 |
| `ONE/SampleFLIRONE.jpg` | FLIR ONE | 120 x 160 (portrait), PNG | ThermImageJ sample image, by Glenn J. Tattersall (https://github.com/gtatters/ThermImageJ) | CC-BY-4.0 |
| `ONE/flir_example.jpg` | FLIR ONE | 240 x 320 (portrait), PNG | `flir_example.jpg` of read_thermal.py (https://github.com/Nervengift/read_thermal.py) | CC0-1.0 |
| `AX8/ax8.jpg` | FLIR AX8 | 80 x 60, PNG | `ax8.jpg` of read_thermal.py (https://github.com/Nervengift/read_thermal.py) | CC0-1.0 |
| `ZenmuseXTR/zenmuse_xtr.jpg` | DJI Zenmuse XT R (FLIR core) | 640 x 512, int16u | `zenmuse_xtr.jpg` of read_thermal.py (https://github.com/Nervengift/read_thermal.py) | CC0-1.0 |
| `XT2/DJI_0087_R.JPG` | DJI Zenmuse XT2 (FLIR core) | 640 x 512, int16u | "Dataset - Thermographic Images Karlsruhe", doi:10.5281/zenodo.7195616, file `automatically recorded drone-based images/Sophienstr. 201-203/Sophienstr. 201-203_Flight 2_45°_40m_3ms/DJI_0087_R.JPG` | CC-BY-4.0 |

CC-BY-4.0: https://creativecommons.org/licenses/by/4.0/ - CC0-1.0: https://creativecommons.org/publicdomain/zero/1.0/
