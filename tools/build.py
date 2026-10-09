#!/usr/bin/env python3
"""Book JSON (content/book{N}.json) → platform activities + answer keys, and the SQL that loads them.

    python3 tools/build.py CONTENT_DIR MEDIA_DIR OUT_DIR [--uz content/uz.json]

Writes
    OUT_DIR/juice-reading-bundle.json   everything in one file, loaded by the teacher in Kutubxona (juice_load RPC)
    OUT_DIR/units/JR1-U01.json …     activity content + answer key per library item (what the platform stores)
    OUT_DIR/sql/10_units_jr{b}.sql    upsert into juice.units (one file per book)
    OUT_DIR/sql/20_media_jr{b}_{k}.sql  upsert into juice.media (book pictures as data URIs, ~1 MB per file)
    OUT_DIR/report.json               counts per unit, used by audit.py

Every unit becomes one Reading activity (picture, listening track, key words, Get Ready warm-up, passage,
then Check Comprehension → Build Vocabulary → Organize Information). Every graded item is either a choice
(the book's options / word bank) or a short typed answer with the accepted forms — all graded by the server.
Get Ready is shown as an ungraded warm-up: many of its answers are opinions or prior knowledge.
Every 4 units the Vocabulary Check becomes its own test; content/tests{N}.json (tools/tests_parse.py)
adds the publisher's Mid-Term and Final tests (JR{N}-MID, JR{N}-FIN).
"""
import base64, difflib, json, os, re, sys

CEFR = {1: 'A1', 2: 'A1', 3: 'A2', 4: 'A2'}
# Printing errors in the book, shown corrected on the platform (listed in the report for the teacher).
TYPOS = [
    (re.compile(r'\bBroadledf\b'), 'Broadleaf'),
    (re.compile(r'\blightening\b'), 'lightning'), (re.compile(r'\bLightening\b'), 'Lightning'),
    (re.compile(r'\bthe life a baby kangaroo\b'), 'the life of a baby kangaroo'),
    (re.compile(r'\bcheery candies\b'), 'cherry candies'),
]
FIXED = []


def fix(o, where=''):
    """Apply TYPOS to every string of a JSON-like value."""
    if isinstance(o, str):
        out = o
        for rx, rep in TYPOS:
            out = rx.sub(rep, out)
        if out != o:
            FIXED.append({'where': where, 'book': o, 'shown': out})
        return out
    if isinstance(o, list):
        return [fix(x, where) for x in o]
    if isinstance(o, dict):
        return {k: fix(v, f'{where}.{k}' if where else k) for k, v in o.items()}
    return o
BLANK = re.compile(r'_{3,}')


def blank_variants(text, n):
    """'It has ___ to let ___ keep the heat.' → one stem per blank: the asked blank stays '___', the others '…'."""
    parts = BLANK.split(text)
    if len(parts) - 1 != n:
        raise ValueError(f'{n} answers but {len(parts) - 1} blanks in: {text}')
    out = []
    for k in range(n):
        s = parts[0]
        for i in range(n):
            s += ('___' if i == k else '…') + parts[i + 1]
        out.append(s)
    return out


def opt_index(options, answer, where):
    norm = lambda x: re.sub(r'\s+', ' ', str(x).strip().lower())
    hits = [i for i, o in enumerate(options) if norm(o) == norm(answer)]
    if len(hits) != 1:
        raise ValueError(f'{where}: answer {answer!r} found {len(hits)}x in {options}')
    return hits[0]


class Unit:
    def __init__(self, code):
        self.code, self.questions, self.key = code, [], {}

    def choice(self, qid, section, task, stem, options, answer, bank=None, img=None, text=None):
        if not (0 <= answer < len(options)):
            raise ValueError(f'{self.code} {qid}: answer {answer} out of range')
        if len(set(o.strip().lower() for o in options)) != len(options):
            raise ValueError(f'{self.code} {qid}: duplicate options {options}')
        q = {'id': qid, 'section': section, 'task': task, 'q': stem, 'options': options}
        if bank:
            q['bank'] = bank
        if img:
            q['img'] = img
        if text:
            q['text'] = text
        self.questions.append(q)
        self.key[qid] = {'a': answer}

    def text(self, qid, section, task, stem, accepted, text=None):
        acc = [a for a in dict.fromkeys(a.strip() for a in accepted) if a]
        if not acc:
            raise ValueError(f'{self.code} {qid}: no accepted answer')
        q = {'id': qid, 'section': section, 'task': task, 'q': stem, 'type': 'text'}
        if text:
            q['text'] = text
        self.questions.append(q)
        self.key[qid] = {'t': acc}


def stem_html(s):
    # a blank reads better as a line; keep the book's words otherwise
    return BLANK.sub('_____', s)


def warmup(gr):
    q1 = gr.get('q1') or {}
    bank = list(q1.get('word_bank') or [])
    for wb in q1.get('word_banks') or []:
        bank += wb.get('words', []) if isinstance(wb, dict) else wb
    items = []
    for it in q1.get('items') or []:
        t = it.get('text', '')
        if q1.get('type') == 'tf' or set(map(str.lower, bank)) == {'true', 'false'}:
            t = f'{t} (True / False)'
        items.append(stem_html(t))
    w = {'prompt': q1.get('prompt', ''), 'bank': [] if set(map(str.lower, bank)) <= {'true', 'false'} else bank, 'items': items}
    sents = [s['text'] if isinstance(s, dict) else s for s in gr.get('listen_sentences') or []]
    if sents:
        w['sentences'] = sents
    return {k: v for k, v in w.items() if v}


def build_unit(b, u, uz, media_ids):
    n = u['unit']
    code, base = f'JR{b}-U{n:02d}', f'jr{b}-u{n:02d}'
    U = Unit(code)
    ci = u.get('comprehension_instructions') or {}
    # Check Comprehension
    for q in u['comprehension']:
        qid, t = f'c{q["n"]}', q['type']
        img = f'{base}-c{q["n"]}' if q.get('pictures') and f'{base}-c{q["n"]}' in media_ids else None
        if t == 'mc':
            opts = list(q['options'])
            if q.get('pictures') and not img:
                raise ValueError(f'{code} {qid}: picture item without a picture crop')
            U.choice(qid, 'Check Comprehension', ci.get('mc', 'Choose the correct answers.'), stem_html(q['stem']), opts, int(q['answer']), img=img)
        elif t == 'tf':
            U.choice(qid, 'Check Comprehension', ci.get('tf', 'Check the correct answers.'), q['stem'], ['True', 'False'], 0 if q['answer'] is True else 1)
        elif t == 'fill':
            U.text(qid, 'Check Comprehension', ci.get('fill', 'Fill in the blanks.'), stem_html(q['stem']), ([q['answer']] if q.get('answer') else []) + list(q.get('accept') or []) + list(q.get('answers') or []))
        else:
            raise ValueError(f'{code}: unknown comprehension type {t}')
    # Build Vocabulary
    bv = u['build_vocab']
    bank = list(bv['word_bank'])
    for it in bv['items']:
        U.choice(f'v{it["n"]}', 'Build Vocabulary', bv.get('instruction', 'Complete the sentences.'), stem_html(it['stem']), bank, opt_index(bank, it['answer'], f'{code} v{it["n"]}'))
    # Organize Information
    org = u['organizer']
    ex = set(x.strip().lower() for x in org.get('example') or [])
    obank = [w for w in org['word_bank'] if w.strip().lower() not in ex]
    k = 0
    task = org.get('instruction', 'Complete the graphic organizer.') + (f' — {org["title"]}' if org.get('title') else '')
    for row in org['rows']:
        ans = row.get('answers') or []
        if not ans:
            continue
        label = (row.get('label') or '').strip()
        for i, stem in enumerate(blank_variants(row['text'], len(ans))):
            k += 1
            shown = f'<b>{label}:</b> {stem_html(stem)}' if label else stem_html(stem)
            U.choice(f'o{k}', 'Organize Information', task, shown, obank, opt_index(obank, ans[i], f'{code} o{k}'))
    words = []
    gl = {g['word'].strip().lower(): g['def'] for g in u.get('glossary') or []}
    lw = u['get_ready'].get('listen_words') or []
    spare = [g for g in gl if g not in [w.strip().lower() for w in lw]]
    for w in lw:
        e, key = {'w': w}, w.strip().lower()
        if uz.get(key):
            e['uz'] = uz[key]
        d = gl.get(key)
        if not d:  # "crawls" → "crawl", "buries" → "bury", "gave birth to" → "give birth to"
            best = difflib.get_close_matches(key, spare, n=1, cutoff=0.6)
            if best:
                d = gl[best[0]]
                spare.remove(best[0])
        if d:
            e['d'] = d
        words.append(e)
    content = {
        'runner': 'reading_quiz', 'level': f'Reading Juice {b}', 'source': code, 'library': True,
        'juice': {'book': b, 'unit': n, 'subject': u.get('subject', '')},
        'image': f'{base}-hero' if f'{base}-hero' in media_ids else None,
        'audio': f'jr{b}/u{n:02d}',          # the passage (publisher CD track 2n+1)
        'audio_words': f'jr{b}/u{n:02d}w',   # Get Ready words, listen and repeat (track 2n)
        'words': words, 'warmup': warmup(u['get_ready']),
        'passage': '\n\n'.join(p.strip() for p in u['passage']),
        'questions': U.questions,
    }
    content = {k2: v for k2, v in content.items() if v not in (None, [], {})}
    return {
        'code': code, 'book': b, 'unit': n, 'kind': 'unit', 'sort': n + (n - 1) // 4,
        'title': f'Reading Juice {b} · Unit {n} — {u["title"]}', 'topic': f'Reading Juice {b}', 'cefr': CEFR[b],
        'items': len(U.questions), 'content': content, 'answer_key': {'items': U.key}, 'audio_path': content['audio'],
    }


def build_check(b, vc, media_ids):
    n = vc['n']
    code, base = f'JR{b}-VC{n}', f'jr{b}-vc{n}'
    U = Unit(code)
    for si, sec in enumerate(vc['sections'], 1):
        t, instr = sec['type'], sec.get('instruction', '')
        name = f'Part {si}'
        if t == 'picture_match':
            opts = list(sec['options'])
            for it in sec['items']:
                img = f'{base}-p{it["n"]}'
                if img not in media_ids:
                    raise ValueError(f'{code}: missing picture {img}')
                U.choice(f'p{it["n"]}', name, instr, f'Picture {it["n"]}', opts, opt_index(opts, it['answer'], f'{code} p{it["n"]}'), img=img)
        elif t == 'match':
            opts = list(sec['options'])
            for it in sec['items']:
                U.choice(f'm{it["n"]}', name, instr, f'<b>{it["stem"]}</b> = ?', opts, opt_index(opts, it['answer'], f'{code} m{it["n"]}'))
        elif t == 'mc':
            for it in sec['items']:
                U.choice(f'c{it["n"]}', name, instr, stem_html(it['stem']), list(it['options']), int(it['answer']))
        elif t == 'cloze':
            bank = list(sec['word_bank'])
            lines = sec['text'].split('\n')
            for key in sorted(sec['answers'], key=int):
                line = next(l for l in lines if f'[{key}]' in l)
                stem = re.sub(r'\[(\d+)\]', lambda m: '_____' if m.group(1) == key else '…', line)
                U.choice(f'd{key}', name, instr, stem, bank, opt_index(bank, sec['answers'][key], f'{code} d{key}'))
        else:
            raise ValueError(f'{code}: unknown section type {t}')
    dialogue = next((s['text'] for s in vc['sections'] if s['type'] == 'cloze'), None)
    content = {
        'runner': 'quiz', 'level': f'Reading Juice {b}', 'source': code, 'library': True,
        'juice': {'book': b, 'check': n},
        'questions': U.questions,
    }
    if dialogue:
        content['passage'] = re.sub(r'\[(\d+)\]', r'(\1) _____', dialogue)
    units = f'{(n - 1) * 4 + 1}–{n * 4}'
    return {
        'code': code, 'book': b, 'unit': None, 'kind': 'check', 'sort': n * 5,
        'title': f'Reading Juice {b} · Vocabulary Check {n} (Units {units})', 'topic': f'Reading Juice {b}', 'cefr': CEFR[b],
        'items': len(U.questions), 'content': content, 'answer_key': {'items': U.key}, 'audio_path': None,
    }


def build_test(b, t):
    """The publisher's Mid-Term / Final test (content/tests{b}.json, from tools/tests_parse.py)."""
    mid = t['kind'] == 'mid'
    code = f'JR{b}-{"MID" if mid else "FIN"}'
    U = Unit(code)
    for g in t['groups']:
        section = f'Questions {g["from"]}–{g["to"]}'
        for it in g['questions']:
            qid = f'q{it["n"]}'
            if it['options']:
                U.choice(qid, section, g['task'], it['q'], list(it['options']), int(it['answer']), text=g['text'] or None)
            else:
                U.text(qid, section, g['task'], it['q'], it['answers'], text=g['text'] or None)
    name = 'Mid-Term Test' if mid else 'Final Test'
    return {
        'code': code, 'book': b, 'unit': None, 'kind': 'test', 'sort': 21 if mid else 22,
        'title': f'Reading Juice {b} · {name}', 'topic': f'Reading Juice {b}', 'cefr': CEFR[b],
        'items': len(U.questions), 'answer_key': {'items': U.key}, 'audio_path': None,
        'content': {'runner': 'quiz', 'level': f'Reading Juice {b}', 'source': code, 'library': True,
                    'juice': {'book': b, 'test': t['kind']}, 'questions': U.questions},
    }


def q(s):
    return "'" + str(s).replace("'", "''") + "'"


def jq(o):
    return q(json.dumps(o, ensure_ascii=False, separators=(',', ':'))) + '::jsonb'


def main(content_dir, media_dir, out_dir, uz_path=None):
    uz = {k.lower(): v for k, v in json.load(open(uz_path)).items()} if uz_path and os.path.exists(uz_path) else {}
    os.makedirs(os.path.join(out_dir, 'units'), exist_ok=True)
    os.makedirs(os.path.join(out_dir, 'sql'), exist_ok=True)
    media_ids = {f[:-4] for f in os.listdir(media_dir) if f.endswith('.jpg')}
    report, bundle = [], {'format': 'juice-reading-bundle', 'version': 1, 'units': [], 'media': []}
    for b in (1, 2, 3, 4):
        path = os.path.join(content_dir, f'book{b}.json')
        if not os.path.exists(path):
            print(f'book {b}: no content yet, skipped')
            continue
        book = fix(json.load(open(path)), f'JR{b}')
        rows = [build_unit(b, u, uz, media_ids) for u in book['units']] + [build_check(b, vc, media_ids) for vc in book.get('vocab_checks', [])]
        tpath = os.path.join(content_dir, f'tests{b}.json')
        if os.path.exists(tpath):
            rows += [build_test(b, t) for t in json.load(open(tpath))['tests']]
        rows.sort(key=lambda r: r['sort'])
        used = set()
        for r in rows:
            json.dump(r, open(os.path.join(out_dir, 'units', f'{r["code"]}.json'), 'w'), ensure_ascii=False, indent=1)
            used |= {r['content'].get('image')} | {x.get('img') for x in r['content']['questions']}
            report.append({'code': r['code'], 'items': r['items'], 'words': len(r['content'].get('words', [])),
                           'uz': sum(1 for w in r['content'].get('words', []) if w.get('uz'))})
        used.discard(None)
        with open(os.path.join(out_dir, 'sql', f'10_units_jr{b}.sql'), 'w') as f:
            f.write(f'-- Reading Juice {b}: {len(rows)} library items (generated by tools/build.py — do not edit)\n')
            for r in rows:
                f.write('insert into juice.units (code, book, unit, kind, sort, title, topic, cefr, items, content, answer_key, audio_path, updated_at) values ('
                        f'{q(r["code"])}, {b}, {r["unit"] if r["unit"] else "null"}, {q(r["kind"])}, {r["sort"]}, {q(r["title"])}, {q(r["topic"])}, {q(r["cefr"])}, {r["items"]}, '
                        f'{jq(r["content"])}, {jq(r["answer_key"])}, {q(r["audio_path"]) if r["audio_path"] else "null"}, now())\n'
                        'on conflict (code) do update set book = excluded.book, unit = excluded.unit, kind = excluded.kind, sort = excluded.sort, title = excluded.title, '
                        'topic = excluded.topic, cefr = excluded.cefr, items = excluded.items, content = excluded.content, answer_key = excluded.answer_key, '
                        'audio_path = excluded.audio_path, updated_at = now();\n')
        part, size, k = [], 0, 1
        def flush():
            nonlocal part, size, k
            if part:
                open(os.path.join(out_dir, 'sql', f'20_media_jr{b}_{k}.sql'), 'w').write(
                    'insert into juice.media (id, data) values\n' + ',\n'.join(part) + '\non conflict (id) do update set data = excluded.data;\n')
                k += 1
            part, size = [], 0
        bundle['units'] += [{k: r[k] for k in ('code', 'book', 'unit', 'kind', 'sort', 'title', 'topic', 'cefr', 'items', 'content', 'answer_key', 'audio_path')} for r in rows]
        for mid in sorted(used):
            data = 'data:image/jpeg;base64,' + base64.b64encode(open(os.path.join(media_dir, mid + '.jpg'), 'rb').read()).decode()
            bundle['media'].append({'id': mid, 'data': data})
            part.append(f'({q(mid)}, {q(data)})')
            size += len(data)
            if size > 900_000:
                flush()
        flush()
        print(f'book {b}: {len(rows)} items, {sum(r["items"] for r in rows)} questions, {len(used)} pictures')
    # one file the teacher loads in Kutubxona → Reading Juice → "Materiallar faylini yuklash"
    json.dump(bundle, open(os.path.join(out_dir, 'juice-reading-bundle.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    json.dump({'units': report, 'typos_corrected': FIXED}, open(os.path.join(out_dir, 'report.json'), 'w'), indent=1, ensure_ascii=False)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    uz = sys.argv[sys.argv.index('--uz') + 1] if '--uz' in sys.argv else None
    if uz in args:
        args.remove(uz)
    main(*args[:3], uz_path=uz)
