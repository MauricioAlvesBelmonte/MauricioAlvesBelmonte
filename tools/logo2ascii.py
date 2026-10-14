import sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
svg, W, H = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
dil = int(sys.argv[4]) if len(sys.argv) > 4 else 0
CW, CH = 18, 40
CHARS = "".join(chr(c) for c in range(33, 127) if chr(c) not in "`") 
font = ImageFont.truetype("/usr/share/fonts/dejavu-sans-mono-fonts/DejaVuSansMono.ttf", 30)
def glyph(c):
    im = Image.new("L", (CW, CH), 0); d = ImageDraw.Draw(im)
    d.text((0, 2), c, font=font, fill=255)
    return np.asarray(im.filter(ImageFilter.GaussianBlur(1.5)), dtype=np.float32) / 255
G = np.stack([glyph(c) for c in CHARS])
Gf = G.reshape(len(CHARS), -1)
png = subprocess.run(["magick", "-background", "white", "-density", "1200", svg, "-resize", "1600x1600", "png:-"], capture_output=True).stdout
import io
im = ImageOps.invert(Image.open(io.BytesIO(png)).convert("L"))
im = im.point(lambda p: 255 if p > 110 else 0)
if dil: im = im.filter(ImageFilter.MaxFilter(dil))
im = im.crop(im.getbbox())
TW, TH = W * CW, H * CH
s = min(TW / im.width, TH / im.height) * 0.96
im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
canvas = Image.new("L", (TW, TH), 0)
canvas.paste(im, ((TW - im.width) // 2, (TH - im.height) // 2))
a = np.asarray(canvas.filter(ImageFilter.GaussianBlur(1.5)), dtype=np.float32) / 255
out = []
for y in range(H):
    row = ""
    for x in range(W):
        cell = a[y*CH:(y+1)*CH, x*CW:(x+1)*CW]
        cov = cell.mean()
        if cov < 0.03: row += " "; continue
        if cov > 0.85: row += "#" if (x + y) % 2 else "@"; continue
        # boost cell so faint edges map to visible strokes
        c = np.clip(cell / max(cell.max(), 1e-3), 0, 1).reshape(-1)
        sc = ((Gf - c) ** 2).sum(1)
        row += CHARS[int(sc.argmin())]
    out.append(row.rstrip())
print("\n".join(out))
