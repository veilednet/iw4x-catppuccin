"""Minimal IW4 .iwi (IWi v8, 32-byte header) reader/writer."""
import struct, io, zipfile, glob, os
from PIL import Image
HDR = struct.Struct("<3sBIBBHHH4i")  # tag, ver, flags, format, unused, w, h, d, sizes[4]
FMT = {1: "ARGB32", 2: "RGB24", 3: "LA16", 4: "L8", 5: "A8", 0xB: "DXT1", 0xC: "DXT3", 0xD: "DXT5"}
def parse(data):
    tag, ver, flags, fmt, _, w, h, d, *sizes = HDR.unpack_from(data)
    assert tag == b"IWi" and ver == 8, (tag, ver)
    return dict(flags=flags, fmt=fmt, w=w, h=h, d=d, sizes=sizes)
def _dds(fmt, w, h, payload):
    fourcc = {0xB: b"DXT1", 0xC: b"DXT3", 0xD: b"DXT5"}[fmt]
    hdr = struct.pack("<4sIIIIIII44xIIII20xI16x", b"DDS ", 124, 0x1007, h, w, 0, 0, 0, 32, 4, struct.unpack("<I", fourcc)[0], 0, 0, 0x1000) if False else None
    head = bytearray(128); head[0:4] = b"DDS "
    struct.pack_into("<IIIIIII", head, 4, 124, 0x1007, h, w, 0, 0, 1)
    struct.pack_into("<II4s", head, 76, 32, 4, fourcc)
    struct.pack_into("<I", head, 108, 0x1000)
    return Image.open(io.BytesIO(bytes(head) + payload))
def mip0_offset(info, data):
    # mips are stored smallest-first; largest level is at the end
    w, h, fmt = info["w"], info["h"], info["fmt"]
    if fmt in (0xB,): size = max(1, (w+3)//4) * max(1, (h+3)//4) * 8
    elif fmt in (0xC, 0xD): size = max(1, (w+3)//4) * max(1, (h+3)//4) * 16
    else: size = w * h * {1: 4, 2: 3, 3: 2, 4: 1, 5: 1}[fmt]
    return len(data) - size, size
def decode(data):
    info = parse(data); off, size = mip0_offset(info, data); px = data[off:off+size]; w, h, f = info["w"], info["h"], info["fmt"]
    if f in (0xB, 0xC, 0xD): return info, _dds(f, w, h, px).convert("RGBA")
    if f == 1: b = Image.frombytes("RGBA", (w, h), px); r_, g_, b_, a_ = b.split(); return info, Image.merge("RGBA", (b_, g_, r_, a_))  # BGRA in file
    if f == 2: b = Image.frombytes("RGB", (w, h), px); r_, g_, b_ = b.split(); return info, Image.merge("RGB", (b_, g_, r_)).convert("RGBA")
    if f == 3: return info, Image.frombytes("LA", (w, h), px).convert("RGBA")
    if f == 4: return info, Image.frombytes("L", (w, h), px).convert("RGBA")
    if f == 5: a = Image.frombytes("L", (w, h), px); im = Image.new("RGBA", (w, h), (255, 255, 255, 0)); im.putalpha(a); return info, im
    raise ValueError(f)
def encode_argb(img, flags=0x3):
    """Write an uncompressed ARGB32 iwi with a full mip chain (smallest first) unless NOMIPMAPS(0x2) is set."""
    img = img.convert("RGBA"); w, h = img.size
    levels = [img]
    if not flags & 0x2:
        while levels[-1].size != (1, 1):
            lw, lh = levels[-1].size; levels.append(levels[-1].resize((max(1, lw//2), max(1, lh//2)), Image.LANCZOS))
    blobs = []
    for lv in levels:
        r, g, b, a = lv.split(); blobs.append(Image.merge("RGBA", (b, g, r, a)).tobytes())
    payload = b"".join(reversed(blobs))  # smallest mip first
    total = HDR.size + len(payload)
    # fileSizeForPicmip[i] = file size when skipping i top mips
    sizes = []
    acc = total
    for i in range(4):
        sizes.append(acc)
        if i < len(blobs) - 1: acc -= len(blobs[i])
    return HDR.pack(b"IWi", 8, flags, 1, 0, w, h, 1, *sizes) + payload
class Index:
    def __init__(self, root):
        self.map = {}
        pats = [os.path.join(root, "main", "iw_*.iwd"), os.path.join(root, "main", "iw4x", "x86", "*.iwd")]
        for pat in pats:
            for p in sorted(glob.glob(pat)):
                z = zipfile.ZipFile(p)
                for n in z.namelist(): self.map[n.replace("\\", "/").lower()] = (p, n)
    def read(self, name):
        p, n = self.map[f"images/{name.lower()}.iwi"]; return zipfile.ZipFile(p).read(n), os.path.basename(p)
