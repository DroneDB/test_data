// Strips the GeoTIFF keys from a LAZ/LAS v1.2+ file header so pdal reports no SRS.
// Usage: node strip-srs.mjs <input.laz> <output.laz>
import { readFileSync, writeFileSync } from 'node:fs';

const [src, dst] = process.argv.slice(2);
const buf = readFileSync(src);
const magic = buf.toString('ascii', 0, 2);
if (magic !== 'LASS') throw new Error('not a LAS/LAZ file');
const publicHeaderLength = buf.readUInt16LE(20);
if (publicHeaderLength < 295) throw new Error('header too short for GeoTIFF keys');

// GeoKeyDirectory size (bytes) is a uint32 at offset 268 of the header.
// Zeroing it (plus the following GeoKeys/DoubleParams data) is enough for
// OGR/pdal to treat the file as having no SRS.
buf.writeInt32LE(0, 268);
buf.fill(0, 272, publicHeaderLength);

writeFileSync(dst, buf);
console.log(`Wrote ${dst} (header length ${publicHeaderLength}, bytes 272..${publicHeaderLength} zeroed)`);
