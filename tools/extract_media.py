#!/usr/bin/env python3
"""Crop the pictures a unit needs from the rendered book pages.

    python3 tools/extract_media.py RENDER_DIR BOOK_JSON OUT_DIR

RENDER_DIR holds `p-07.png` … (pdftoppm -r 200 output of one book). For every unit:
  * jr{b}-u{nn}-hero.jpg  the unit photo with its title (top of the first page, down to the first white gap)
  * jr{b}-u{nn}-c{n}.jpg  the picture options of a Check Comprehension item (pictures + their a/b/c captions)
For every vocabulary check:
  * jr{b}-vc{n}-p{k}.jpg  each picture of "Match the pictures with the words"
Detection is geometric: rows/columns that are not near-white form picture blocks; text lines are short, pictures tall.
A manifest (media.json) lists every crop with its pixel box so a reviewer can re-check it on a contact sheet.
"""
import json, os, re, subprocess, sys
from PIL import Image

WHITE = 232          # a pixel brighter than this in every channel counts as background
MIN_PIC = 120        # px at 200 dpi: anything taller is a picture band, shorter is a text line


def ink_rows(img, x0=0, x1=None, thr=0.06):
    g = img.convert('L')
    w, h = g.size
    x1 = x1 or w
    px = g.load()
    step = 3
    rows = []
    for y in range(h):
        n = tot = 0
        for x in range(x0, x1, step):
            tot += 1
            if px[x, y] < WHITE:
                n += 1
        rows.append(n / tot > thr)
    return rows


def bands(flags, min_len, gap=8):
    """Runs of True (allowing gaps shorter than `gap`) at least `min_len` long → [(start, end)]."""
    out, start, last = [], None, None
    for i, f in enumerate(flags):
        if f:
            if start is None:
                start = i
            last = i
        elif start is not None and i - last > gap:
            if last - start >= min_len:
                out.append((start, last))
            start = None
    if start is not None and last - start >= min_len:
        out.append((start, last))
    return out


def ink_cols(img, y0, y1, thr=0.04):
    g = img.convert('L').crop((0, y0, img.width, y1))
    px = g.load()
    cols = []
    for x in range(g.width):
        n = sum(1 for y in range(0, g.height, 3) if px[x, y] < WHITE)
        cols.append(n / max(1, g.height // 3) > thr)
    return cols


def save(img, box, path, width):
    c = img.crop(box).convert('RGB')
    if c.width > width:
        c = c.resize((width, round(c.height * width / c.width)), Image.LANCZOS)
    c.save(path, 'JPEG', quality=68, optimize=True, progressive=True)
    return os.path.getsize(path)


def ocr_lines(img, scale=2):
    """Text lines on the page: [(text, x0, y0, x1, y1)] via tesseract (half resolution is usually plenty)."""
    small = img.convert('L').resize((img.width // scale, img.height // scale))
    tmp = os.path.join(os.environ.get('TMPDIR', '/tmp'), f'jr-ocr-{os.getpid()}.png')
    small.save(tmp)
    tsv = subprocess.run(['tesseract', tmp, '-', '--psm', '3', 'tsv'], capture_output=True, text=True).stdout
    lines = {}
    for row in tsv.splitlines()[1:]:
        f = row.split('\t')
        if len(f) < 12 or not f[11].strip():
            continue
        k = (f[2], f[3], f[4])
        x, y, w, h = (int(v) * scale for v in f[6:10])
        t = lines.setdefault(k, [[], x, y, x + w, y + h])
        t[0].append(f[11]); t[1] = min(t[1], x); t[2] = min(t[2], y); t[3] = max(t[3], x + w); t[4] = max(t[4], y + h)
    return sorted(((' '.join(v[0]), v[1], v[2], v[3], v[4]) for v in lines.values()), key=lambda l: l[2])


NUM = re.compile(r'^\(?(\d{1,2})\s*[.:;,)]')
HEAD = re.compile(r'^(Check|Fill|Choose|Read|Write|Circle|Number|Complete|Match|Answer|Put)\b', re.I)


def hero_box_ocr(img, lines):
    h = img.height
    for t, x0, y0, x1, y1 in lines:
        if y0 > h * 0.3 and re.search(r'Get\s*Ready', t, re.I):
            # the title art sometimes hangs over the "Get Ready" row on the right: follow it down
            flags = ink_rows(img, int(img.width * 0.45), int(img.width * 0.98), thr=0.02)
            y, blank = y0 - 14, 0
            while y < min(h - 1, y0 + 160) and blank < 10:
                y += 1
                blank = blank + 1 if not flags[y] else 0
            return (0, int(h * 0.012), img.width, max(y0 - 14, y - blank - 10))
    nums = [l for l in lines if l[2] > h * 0.35 and NUM.match(l[0]) and l[1] < img.width * 0.3]
    if nums:
        return (0, int(h * 0.012), img.width, nums[0][2] - 110)
    return hero_box(img)


def item_lines(img, lines):
    """Item stems of a question page, in order. OCR often misreads the number itself ("3:" or "i."), so stems are
    found by position: they start at the same x as item 1, and section headings are excluded."""
    W = img.width
    first = next((l for l in lines if l[1] < W * 0.3 and (m := NUM.match(l[0])) and int(m.group(1)) == 1), None)
    if not first:
        return []
    return [l for l in lines if l[2] >= first[2] and abs(l[1] - first[1]) < 36 and not HEAD.match(l[0])]


def question_band(img, lines, n):
    """Area between the stem of item n and the next stem / section heading (its pictures + captions)."""
    W = img.width
    stems = item_lines(img, lines)
    if len(stems) < n - 1 or n < 2 and not stems:
        return None
    if len(stems) >= n and (n == len(stems) or stems[n][2] > stems[n - 1][4]):
        top = stems[n - 1][4] + 6
    else:
        # stem n was not read at all: it is the 2nd short text band after the pictures of item n-1
        # (pictures, their captions, then the stem line)
        prev = stems[n - 2]
        heads = [l for l in lines if l[2] > prev[4] + 40 and HEAD.match(l[0]) and l[1] < W * 0.22]
        stop = heads[0][2] if heads else int(img.height * 0.93)
        flags = ink_rows(img, int(W * 0.1), int(W * 0.9), thr=0.01)
        bs = [(a + prev[4], c + prev[4]) for a, c in bands(flags[prev[4]:stop], 10, gap=6)]
        seen_tall, shorts = False, 0
        top = None
        for a, c in bs:
            if c - a > 120:
                seen_tall = True
            elif seen_tall:
                shorts += 1
                if shorts == 2:
                    top = c + 6
                    break
        if top is None:
            return None
        nxt = next((l for l in lines if l[2] > top + 40 and l[1] < W * 0.22 and (l in stems or HEAD.match(l[0]))), None)
        return (top, (nxt[2] - 8) if nxt else stop - 8)
    nxt = next((l for l in lines if l[2] > top + 40 and l[1] < W * 0.22 and (l in stems or HEAD.match(l[0]))), None)
    bottom = (nxt[2] - 8) if nxt else int(img.height * 0.93)
    return (top, bottom)


def tall_bands(img, xa, xb):
    """Picture rows below the page heading: ink bands taller than 150 px (frames count, so white-backed photos too)."""
    H = img.height
    flags = ink_rows(img, int(img.width * xa), int(img.width * xb), thr=0.003 if xb > 0.9 else 0.01)
    y0 = int(H * 0.2)
    return [(a + y0, c + y0) for a, c in bands(flags[y0:int(H * 0.95)], 10, gap=10) if c - a > 150]


def with_caption(img, s0, e0):
    """Add the caption row printed right under a picture row (if any, within 60 px)."""
    flags = ink_rows(img, int(img.width * 0.08), int(img.width * 0.95), thr=0.003)
    nxt = bands(flags[e0 + 1:e0 + 160], 8, gap=6)
    if nxt and nxt[0][0] < 60 and nxt[0][1] - nxt[0][0] < 70:
        return (s0, e0 + 1 + nxt[0][1])
    return (s0, e0)


def hero_box(img):
    """From the page top to the first long white gap below 35 % of the page: photo + title art."""
    h = img.height
    flags = ink_rows(img, int(img.width * 0.08), int(img.width * 0.92), thr=0.5)
    y = int(h * 0.35)
    run = 0
    while y < int(h * 0.75):
        run = run + 1 if not flags[y] else 0
        if run >= 18:
            return (0, int(h * 0.012), img.width, y - run)
        y += 1
    return (0, int(h * 0.012), img.width, int(h * 0.56))


def picture_bands(img, top_frac=0.07, bottom_frac=0.95):
    h = img.height
    flags = ink_rows(img, int(img.width * 0.08), int(img.width * 0.95), thr=0.18)
    y0, y1 = int(h * top_frac), int(h * bottom_frac)
    out = []
    for s, e in bands(flags[y0:y1], MIN_PIC):
        out.append((s + y0, e + y0))
    return out


def with_captions(img, s, e):
    """Extend a picture band down over the caption line(s) right under it."""
    flags = ink_rows(img, int(img.width * 0.08), int(img.width * 0.95), thr=0.01)
    y, blank = e, 0
    while y < min(img.height - 1, e + 110):
        y += 1
        blank = blank + 1 if not flags[y] else 0
        if blank >= 14 and y - e > 30:
            break
    return (s, max(e, y - blank))


def trim_x(img, s, e, pad=16):
    cols = ink_cols(img, s, e)
    xs = [i for i, f in enumerate(cols) if f]
    if not xs:
        return (0, img.width)
    return (max(0, xs[0] - pad), min(img.width, xs[-1] + pad))


def main(render_dir, book_json, out_dir):
    book = json.load(open(book_json))
    b = book['book']
    os.makedirs(out_dir, exist_ok=True)
    page = lambda n: Image.open(os.path.join(render_dir, f'p-{n:02d}.png'))
    manifest, problems = [], []

    for u in book['units']:
        n, p0 = u['unit'], u['pdf_page']
        base = f'jr{b}-u{n:02d}'
        img = page(p0)
        box = hero_box_ocr(img, ocr_lines(img))
        manifest.append({'id': f'{base}-hero', 'page': p0, 'box': box, 'bytes': save(img, box, os.path.join(out_dir, f'{base}-hero.jpg'), 760)})
        pics = [q for q in u.get('comprehension', []) if q.get('pictures')]
        if pics:
            cimg = page(p0 + 2)
            found = tall_bands(cimg, 0.08, 0.95)
            if len(found) != len(pics):
                problems.append(f'{base}: {len(pics)} picture questions, {len(found)} picture rows on p.{p0 + 2}')
            for q, (s0, e0) in zip(pics, found):
                s2, e2 = with_caption(cimg, s0, e0)
                x0, x1 = trim_x(cimg, s2, e2)
                box = (x0, s2 - 8, x1, e2 + 8)
                manifest.append({'id': f'{base}-c{q["n"]}', 'page': p0 + 2, 'box': box, 'bytes': save(cimg, box, os.path.join(out_dir, f'{base}-c{q["n"]}.jpg'), 640)})

    for vc in book.get('vocab_checks', []):
        sec = next((s for s in vc['sections'] if s['type'] == 'picture_match'), None)
        if not sec:
            continue
        img = page(vc['pdf_page'])
        found = tall_bands(img, 0.12, 0.5)
        if len(found) < len(sec['items']):
            problems.append(f'jr{b}-vc{vc["n"]}: {len(sec["items"])} pictures expected, {len(found)} found')
        for it, (s0, e0) in zip(sec['items'], found):
            cols = ink_cols(img, s0, e0)
            xs = [i for i, f in enumerate(cols[:int(img.width * 0.5)]) if f and i > img.width * 0.14]
            x0, x1 = (xs[0] - 8, xs[-1] + 8) if xs else (0, img.width // 2)
            box = (x0, s0 - 6, x1, e0 + 6)
            manifest.append({'id': f'jr{b}-vc{vc["n"]}-p{it["n"]}', 'page': vc['pdf_page'], 'box': box, 'bytes': save(img, box, os.path.join(out_dir, f'jr{b}-vc{vc["n"]}-p{it["n"]}.jpg'), 420)})

    json.dump({'book': b, 'media': manifest, 'problems': problems}, open(os.path.join(out_dir, f'media-jr{b}.json'), 'w'), indent=1)
    print(f'book {b}: {len(manifest)} crops, {sum(m["bytes"] for m in manifest) // 1024} KB')
    for p in problems:
        print('  !', p)


if __name__ == '__main__':
    main(*sys.argv[1:4])
