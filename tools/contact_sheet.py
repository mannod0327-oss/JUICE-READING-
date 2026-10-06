#!/usr/bin/env python3
"""Contact sheet of crops for a visual check: python3 tools/contact_sheet.py MEDIA_DIR PREFIX OUT.png"""
import os, sys
from PIL import Image, ImageDraw
d, prefix, out = sys.argv[1:4]
files = sorted(f for f in os.listdir(d) if f.startswith(prefix) and f.endswith('.jpg'))
W, H, cols = 300, 200, 6
rows = (len(files) + cols - 1) // cols
sheet = Image.new('RGB', (cols * W, rows * (H + 18)), 'white')
dr = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    im = Image.open(os.path.join(d, f)); im.thumbnail((W - 6, H - 6))
    x, y = (i % cols) * W, (i // cols) * (H + 18)
    sheet.paste(im, (x + 3, y + 3)); dr.text((x + 4, y + H + 2), f[:-4], fill='black')
sheet.save(out); print(len(files), 'images')
