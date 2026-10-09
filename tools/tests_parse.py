"""Parse the publisher's "Mid & Final Test" documents into content/tests{b}.json.

Usage: python3 tools/tests_parse.py TXT_DIR   (TXT_DIR holds t1.txt..t4.txt, from
       `soffice --headless --convert-to txt:Text` of the .doc files)
Each test ends with an "Answers:" line; the parser fails unless every question
has exactly one answer and every choice answer is among its options.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROUP = re.compile(r'^\[(\d+)-(\d+)\]\s*(.*?)\s*(?:\[from[^\]]*\]+)?\s*$')
QNUM = re.compile(r'^\s*(\d+)\.\s+(.*\S)\s*$')
BLANK = '_____'
# Source typos fixed for children (publisher text otherwise kept verbatim).
TYPOS = [('sigh papers', 'sign papers'), ('vocanoes', 'volcanoes'), ('The mail mosquito', 'The male mosquito'),
         ('Scientist study', 'Scientists study'), ('What do scientist use', 'What do scientists use'),
         ('The chef sued', 'The chef used'), ('the cheese cal roll', 'the cheese can roll'),
         ('Louis need a better to read', 'Louis needed a better way to read'), ('Rosa Park?', 'Rosa Parks?'), ('Rosa Park was', 'Rosa Parks was'),
         ('What has changed because of Rosa', 'What has changed because of Rosa?'),
         ('It can slower than', 'It ran slower than'), ('What can we more likely to see', 'What are we more likely to see'),
         ('becojmes', 'becomes')]
# Layout glitches in the source documents, fixed before parsing.
SOURCE = [('8. lava, a volcano', '8. lava / a volcano'),
          ('14. c   16. b', '14. c   15. b'),  # Lv4 mid: key skips 15; the passage answer is b
          # " | " ends an "A / B" choice that sits mid-sentence
          ('9. Water vapor / A rain drop goes up', '9. Water vapor / A rain drop | goes up'),
          ('10. The water becomes 10.  water vapor', 'The water becomes 10. water vapor'),
          ('7. covers / breaks its bones', '7. covers / breaks | its bones'),
          ('_______________.  are homes', '_______________ are homes')]
# Extra accepted forms for open (text) answers: (book, test, n) -> list
ACCEPT = {(4, 'final', 10): ['olive oil', 'olive oil, water and egg yolk', 'oil, water, and egg yolk'],
          (4, 'final', 9): ['no cream']}


def fix(s):
    for a, b in TYPOS:
        s = s.replace(a, b)
    return re.sub(r'\s+([.,!?])', r'\1', re.sub(r'\s+', ' ', s)).strip()


def norm(s):
    return re.sub(r'[^a-z0-9 ]', '', re.sub(r'\s+', ' ', s.lower())).strip()


def parse_answers(text):
    text = re.sub(r'\s+', ' ', text)
    return {int(m.group(1)): m.group(2).strip()
            for m in re.finditer(r'(\d+)\.?\s+(.*?)(?=\s+\d+\.?\s+\S|$)', text)}


def split_tests(lines):
    tests, cur = [], None
    for ln in lines:
        if re.match(r'^(Mid-Term|Final) Test\s*$', ln.strip()):
            cur = {'kind': 'mid' if ln.strip().startswith('Mid') else 'final', 'lines': []}
            tests.append(cur)
        elif cur is not None:
            cur['lines'].append(ln)
    return tests


def parse_test(book, kind, lines):
    body, ans = [], ''
    for i, ln in enumerate(lines):
        if ln.startswith('Answers:'):
            tail = []
            for t in lines[i:]:
                if 'Reading Juice for Kids' in t:
                    break
                tail.append(t)
            ans = ' '.join(tail)[len('Answers:'):]
            break
        body.append(ln)
    answers = parse_answers(ans)
    groups, g = [], None
    for ln in body:
        m = GROUP.match(ln.strip())
        if m:
            g = {'from': int(m.group(1)), 'to': int(m.group(2)), 'task': m.group(3), 'raw': []}
            groups.append(g)
        elif g is not None and ln.strip() and 'Reading Juice for Kids' not in ln:
            g['raw'].append(ln.rstrip())
    out = [parse_group(book, kind, g, answers) for g in groups]
    n = sum(len(x['questions']) for x in out)
    assert n == len(answers) == out[-1]['to'], (book, kind, n, len(answers))
    return {'kind': kind, 'groups': out}


INL_BLANK = re.compile(r'\b(\d+)\.\s*_{3,}')
INL_CHOICE = re.compile(r'\b(\d+)\.\s*([^/|]+?)\s*/\s*([^|]+?)\s*(?=\s\|\s|\.\s*$|\s*$)')


def parse_group(book, kind, g, answers):
    task, raw, lo, hi = g['task'], g['raw'], g['from'], g['to']
    inside = lambda n: lo <= n <= hi
    fill = task.lower().startswith('fill')
    bank = []
    if fill:  # first line(s) with words separated by wide gaps form the bank
        while raw and re.search(r'\S\s{3,}\S', raw[0]) and not QNUM.match(raw[0]) and '___' not in raw[0]:
            bank += [w.strip() for w in re.split(r'\s{3,}', raw.pop(0).strip()) if w.strip()]
    qs, text = [], []
    i = 0
    while i < len(raw):
        ln = raw[i]
        qm = QNUM.match(ln)
        if qm and inside(int(qm.group(1))) and not ln.startswith(' ') and '/' not in ln and int(qm.group(1)) not in [q['n'] for q in qs]:
            n, stem, opts = int(qm.group(1)), qm.group(2), []
            while i + 1 < len(raw) and raw[i + 1].lstrip().startswith('?'):
                i += 1
                o = raw[i].lstrip()[1:].strip()
                opts += ['True', 'False'] if re.match(r'^True\s+\?\s*False$', o) else [re.sub(r'^[a-c]\.\s*', '', o)]
            stem = re.sub(r'_{3,}', BLANK, stem)
            qs.append({'n': n, 'q': fix(stem), 'options': bank if fill else [fix(o) for o in opts]})
        else:
            # blanks or "A / B" choices inside a passage / organizer line
            for m in INL_BLANK.finditer(ln):
                n = int(m.group(1))
                if inside(n):
                    qs.append({'n': n, 'q': sentence(ln, n), 'options': bank})
            m = INL_CHOICE.search(ln)
            if m and inside(int(m.group(1))):
                qs.append({'n': int(m.group(1)), 'q': sentence(ln, int(m.group(1))), 'options': [fix(m.group(2)), fix(m.group(3))]})
            shown = INL_BLANK.sub(lambda m: f'({m.group(1)}) {BLANK}' if inside(int(m.group(1))) else m.group(0), ln)
            shown = INL_CHOICE.sub(lambda m: f'({m.group(1)}) {BLANK}' if inside(int(m.group(1))) else m.group(0), shown)
            if shown.strip() not in ('?',):
                text.append(fix(shown.replace(' | ', ' ')))
        i += 1
    qs.sort(key=lambda q: q['n'])
    assert [q['n'] for q in qs] == list(range(lo, hi + 1)), (book, kind, lo, hi, [q['n'] for q in qs])
    for q in qs:
        a = answers[q['n']]
        if not q['options']:
            q['answers'] = [fix(a)] + ACCEPT.get((book, kind, q['n']), [])
            continue
        k = [norm(o) for o in q['options']]
        a2 = {'t': 'true', 'f': 'false'}.get(norm(a), norm(a))
        if len(a2) == 1 and a2 in 'abc' and len(k) == 3 and q['options'] is not bank:
            q['answer'] = 'abc'.index(a2)
        else:
            hit = [j for j, o in enumerate(k) if o == a2 or o.rstrip('s') == a2.rstrip('s')]
            assert len(hit) == 1, (book, kind, q['n'], a, q['options'])
            q['answer'] = hit[0]
    return {'from': lo, 'to': hi, 'task': fix(task), 'bank': bank, 'text': '\n'.join(t for t in text if t), 'questions': qs}


def sentence(ln, n):
    """The sentence of `ln` that holds item n, with its gap shown as _____ and other gaps as …"""
    parts = re.split(r'(?<=[A-Za-z\'")][.!?])\s+(?=[A-Z])', fix(ln))
    mine = next((p for p in parts if re.search(rf'\b{n}\.\s', p)), fix(ln))
    mine = re.sub(rf'\b{n}\.\s*(_{{3,}}|[^/|]+?\s*/\s*[^|]+?(?=\s\|\s|\.?\s*$))', BLANK, mine).replace(' | ', ' ')
    mine = re.sub(r'\b\d+\.\s*_{3,}', '…', mine)
    return re.sub(r'^\s*[-•]\s*', '', mine).strip()


if __name__ == '__main__':
    d = sys.argv[1]
    for b in (1, 2, 3, 4):
        src = open(os.path.join(d, f't{b}.txt'), encoding='utf-8-sig').read().replace('\xa0', ' ')
        for a, z in SOURCE:
            src = src.replace(a, z)
        lines = src.splitlines()
        tests = [parse_test(b, t['kind'], t['lines']) for t in split_tests(lines)]
        assert [t['kind'] for t in tests] == ['mid', 'final']
        json.dump({'book': b, 'tests': tests}, open(os.path.join(ROOT, 'content', f'tests{b}.json'), 'w'), ensure_ascii=False, indent=1)
        print(f'book {b}: ' + ', '.join(f"{t['kind']} {sum(len(g['questions']) for g in t['groups'])} q" for t in tests))
