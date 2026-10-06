#!/usr/bin/env python3
"""Audit the built library items (out/units/*.json) before they are loaded into Supabase.

    python3 tools/audit.py OUT_DIR MEDIA_DIR

Checks, per item:
  A1 every question has a unique id and a key entry; every key entry belongs to a question
  A2 choice: 2+ options, no duplicates, key index in range
  A3 text: at least one accepted answer; for a unit, each accepted answer (or its first word) occurs in the passage
  A4 every picture the item uses (hero, question pictures) exists in MEDIA_DIR
  A5 grading the key itself with the server's rules (submit-assignment normText/textOk) gives 100 %,
     and an empty paper gives 0 %
  A6 a unit has a passage, a hero picture, a listening track path and 8+ questions; a check has 12+ questions
Prints a summary and exits 1 if anything fails.
"""
import json, os, re, sys


# Reviewed by hand: the answer is implied by the passage but not written in it.
KNOWN = {
    ('JR3-U13', 'c4'): "\"Wasps and bees look similar, but they are not the ___.\" — the passage ends \"they are not\" (the same).",
}


def norm(v):
    v = str(v or '').lower()
    v = re.sub(r"[’‘ʻʼ`]", "'", v)
    v = re.sub(r'[.,!?;:()\[\]{}"]', ' ', v)
    return re.sub(r'\s+', ' ', v).strip()


def text_ok(resp, accepted):  # same rule as supabase/functions/submit-assignment
    r = norm(resp)
    if not r:
        return False
    for raw in accepted:
        a = norm(raw)
        if not a:
            continue
        if r == a:
            return True
        rt, at = set(r.split()), set(a.split())
        hit = len([x for x in at if x in rt])
        if at and hit / len(at) >= 0.9 and len(rt) / len(at) >= 0.7:
            return True
    return False


def grade(qs, key, answers):
    ok = 0
    for q, a in zip(qs, answers):
        k = key[q['id']]
        if q.get('type') == 'text':
            ok += text_ok(a, k['t'])
        else:
            ok += a == k['a']
    return round(100 * ok / len(qs))


def main(out_dir, media_dir):
    media = {f[:-4] for f in os.listdir(media_dir) if f.endswith('.jpg')}
    files = sorted(f for f in os.listdir(os.path.join(out_dir, 'units')) if f.endswith('.json'))
    problems, totals = [], {'items': 0, 'questions': 0, 'choice': 0, 'text': 0, 'pictures': 0}
    for f in files:
        r = json.load(open(os.path.join(out_dir, 'units', f)))
        code, c, key = r['code'], r['content'], r['answer_key']['items']
        qs = c['questions']
        bad = lambda m: problems.append(f'{code}: {m}')
        ids = [q['id'] for q in qs]
        if len(set(ids)) != len(ids):
            bad('A1 duplicate question ids')
        if set(ids) != set(key):
            bad(f'A1 key/question mismatch {set(ids) ^ set(key)}')
        passage = norm(c.get('passage', ''))
        for q in qs:
            k = key.get(q['id'], {})
            if q.get('type') == 'text':
                totals['text'] += 1
                if not k.get('t'):
                    bad(f'A3 {q["id"]} no accepted answer')
                elif r['kind'] == 'unit' and (code, q['id']) not in KNOWN and not any(norm(a) in passage or norm(a).split()[0] in passage.split() for a in k['t']):
                    bad(f'A3 {q["id"]} answer {k["t"]} not found in passage')
            else:
                totals['choice'] += 1
                o = q.get('options') or []
                if len(o) < 2 or len(set(map(norm, o))) != len(o):
                    bad(f'A2 {q["id"]} options {o}')
                if not isinstance(k.get('a'), int) or not 0 <= k['a'] < len(o):
                    bad(f'A2 {q["id"]} key {k.get("a")} out of range')
            if q.get('img'):
                totals['pictures'] += 1
                if q['img'] not in media:
                    bad(f'A4 missing picture {q["img"]}')
        if c.get('image') and c['image'] not in media:
            bad(f'A4 missing hero {c["image"]}')
        right = [key[q['id']]['t'][0] if q.get('type') == 'text' else key[q['id']]['a'] for q in qs]
        empty = ['' if q.get('type') == 'text' else -1 for q in qs]
        if grade(qs, key, right) != 100:
            bad('A5 key does not grade 100 %')
        if grade(qs, key, empty) != 0:
            bad('A5 empty paper does not grade 0 %')
        if r['kind'] == 'unit':
            if not (c.get('passage') and c.get('image') and c.get('audio') and len(qs) >= 8):
                bad(f'A6 incomplete unit (passage/image/audio/{len(qs)} questions)')
        elif len(qs) < 12:
            bad(f'A6 check has only {len(qs)} questions')
        totals['items'] += 1
        totals['questions'] += len(qs)
    print(json.dumps(totals))
    for p in problems:
        print('  !', p)
    print(f'DEFECTS: {len(problems)} · KNOWN: {len(KNOWN)} (' + '; '.join(f'{a} {b}: {w}' for (a, b), w in KNOWN.items()) + ')')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:3]))
