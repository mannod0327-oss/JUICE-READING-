"""Publisher audio (ReadingJuiceforKidsSB1_MP3.ZIP … SB4) → the names the pages and the platform use.

Usage: python3 tools/audio_pack.py OUT_DIR ZIP [ZIP …]
The CD has 33 tracks per book: RJK_<book>-01 is the intro, then two per unit — even = the unit's
Get Ready words (listen and repeat), odd = the passage (checked against word counts: the odd tracks
follow passage length, r = 0.74–0.82). Writes jr<book>-u<NN>.mp3 (passage) and jr<book>-u<NN>w.mp3 (words).
Same mapping as TE.learner.juiceTrack in the platform.
"""
import os, re, sys, zipfile


def target(name):
    m = re.search(r'RJK_([1-4])-(\d{2})\.mp3$', name, re.I)
    if not m:
        return None
    b, t = int(m.group(1)), int(m.group(2))
    if not 2 <= t <= 33:
        return None
    return f'jr{b}-u{t // 2:02d}{"" if t % 2 else "w"}.mp3'


def main(out, zips):
    os.makedirs(out, exist_ok=True)
    done = {}
    for z in zips:
        with zipfile.ZipFile(z) as zf:
            for info in zf.infolist():
                name = target(info.filename)
                if name:
                    with zf.open(info) as src, open(os.path.join(out, name), 'wb') as dst:
                        dst.write(src.read())
                    done[name] = info.filename
    want = {f'jr{b}-u{u:02d}{w}.mp3' for b in (1, 2, 3, 4) for u in range(1, 17) for w in ('', 'w')}
    missing = sorted(want - set(done))
    print(f'{len(done)} tracks → {out}' + (f'; missing {len(missing)}: {", ".join(missing[:8])}…' if missing else ' (all 128)'))
    return 1 if missing else 0


if __name__ == '__main__':
    assert target('RJK_Book1/RJK_1-02.mp3') == 'jr1-u01w.mp3' and target('RJK_4-33.mp3') == 'jr4-u16.mp3'
    assert target('RJK_1-01.mp3') is None and target('_VUC69~7') is None
    sys.exit(main(sys.argv[1], sys.argv[2:]))
