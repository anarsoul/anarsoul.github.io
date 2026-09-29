#!/usr/bin/env python3
"""Find and remove GPS coordinates from JPEG EXIF, losslessly.

Usage:
  strip_gps.py FILE...          strip GPS from files, print the ones changed
  strip_gps.py --check FILE...  only report files with GPS, exit 1 if any

The GPS IFD is emptied in place and all of its data is zeroed, so image
data and other metadata (including orientation) stay untouched. No
third-party dependencies.
"""
import re
import struct
import sys

GPS_IFD_TAG = 0x8825
TYPE_SIZES = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8}
XMP_GPS = re.compile(rb"exif:GPS(Latitude|Longitude)")


def exif_segments(data):
    """Yield (start, end) of the TIFF payload of each Exif APP1 segment."""
    if data[:2] != b"\xff\xd8":
        return
    i = 2
    while i + 4 <= len(data):
        if data[i] != 0xFF:
            return
        marker = data[i + 1]
        if marker in (0xD9, 0xDA):  # EOI / start of scan: no more metadata
            return
        length = struct.unpack(">H", data[i + 2:i + 4])[0]
        body = i + 4
        if marker == 0xE1 and data[body:body + 6] == b"Exif\x00\x00":
            yield body + 6, i + 2 + length
        i += 2 + length


def gps_ifd(buf, tiff, end):
    """Return (endian, gps_ifd_offset) if the TIFF block has a GPS IFD."""
    order = buf[tiff:tiff + 2]
    if order not in (b"II", b"MM"):
        return None
    e = "<" if order == b"II" else ">"
    ifd0 = tiff + struct.unpack(e + "I", buf[tiff + 4:tiff + 8])[0]
    if ifd0 + 2 > end:
        return None
    count = struct.unpack(e + "H", buf[ifd0:ifd0 + 2])[0]
    for n in range(count):
        entry = ifd0 + 2 + 12 * n
        tag = struct.unpack(e + "H", buf[entry:entry + 2])[0]
        if tag == GPS_IFD_TAG:
            off = tiff + struct.unpack(e + "I", buf[entry + 8:entry + 12])[0]
            if off + 2 <= end and struct.unpack(e + "H", buf[off:off + 2])[0] > 0:
                return e, off
    return None


def has_gps(data):
    if XMP_GPS.search(data):
        return True
    return any(gps_ifd(data, s, t) for s, t in exif_segments(data))


def strip(data):
    buf = bytearray(data)
    for tiff, end in exif_segments(data):
        found = gps_ifd(buf, tiff, end)
        if not found:
            continue
        e, off = found
        count = struct.unpack(e + "H", buf[off:off + 2])[0]
        for n in range(count):
            entry = off + 2 + 12 * n
            typ, cnt = struct.unpack(e + "HI", buf[entry + 2:entry + 8])
            size = TYPE_SIZES.get(typ, 1) * cnt
            if size > 4:  # value lives outside the entry: wipe it too
                val = tiff + struct.unpack(e + "I", buf[entry + 8:entry + 12])[0]
                if val + size <= end:
                    buf[val:val + size] = bytes(size)
            buf[entry:entry + 12] = bytes(12)
        buf[off:off + 2] = bytes(2)  # the GPS IFD now has zero entries
    return bytes(buf)


def main(argv):
    check = argv[:1] == ["--check"]
    files = argv[1:] if check else argv
    bad = []
    for path in files:
        with open(path, "rb") as f:
            data = f.read()
        if not has_gps(data):
            continue
        if not check:
            data = strip(data)
            with open(path, "wb") as f:
                f.write(data)
            if XMP_GPS.search(data):
                print(f"{path}: GPS in XMP metadata, remove it manually", file=sys.stderr)
                bad.append(path)
                continue
        print(path)
        if check:
            bad.append(path)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
