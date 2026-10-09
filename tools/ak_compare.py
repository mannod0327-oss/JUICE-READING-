"""Compare content/book{1-4}.json against the publisher's Answer Key PDFs.

Usage: python3 tools/ak_compare.py AK_DIR   (AK_DIR holds ak1.pdf..ak4.pdf)
The answer keys have a text layer; each PDF page has two book-page columns.
Writes build/ak_report.json and prints mismatches.
"""
import html, json, os, re, subprocess, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPLIT_X = 262  # column boundary in pt (page width 524)
WORD = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>')
NUM = re.compile(r'^(\d+)\.\s*(.+)$')
PAGE = re.compile(r'^p\.\s*(\d+)$')


def norm(s):
    s = s.replace('’’', "'").replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    return re.sub(r'\s+', ' ', re.sub(r'[.,!?;:"]', ' ', s.lower())).strip()


def columns(pdf):
    """Yield each text line of each column, as a list of gap-separated chunks."""
    out = subprocess.run(['pdftotext', '-bbox', pdf, '-'], capture_output=True, text=True, check=True).stdout
    for page in out.split('<page')[1:]:
        words = [(float(a), float(b), float(c), html.unescape(t)) for a, b, c, _, t in WORD.findall(page)]
        for left in (True, False):
            col = sorted((w for w in words if (w[0] < SPLIT_X) == left), key=lambda w: (w[1], w[0]))
            lines = []
            for w in col:
                if lines and abs(w[1] - lines[-1][0][1]) <= 3:
                    lines[-1].append(w)
                else:
                    lines.append([w])
            for ln in lines:
                ln.sort()
                chunks, chunk, last = [], [], None
                for x0, _, x1, t in ln:
                    if last is not None and x0 - last > 12:
                        chunks.append(' '.join(chunk)); chunk = []
                    chunk.append(t); last = x1
                chunks.append(' '.join(chunk))
                yield chunks


def parse(pdf):
    """page -> {'num': [(section, n, answer)], 'free': [text]}"""
    data = defaultdict(lambda: {'num': [], 'free': []})
    page, section = None, ''
    for chunks in columns(pdf):
        line = ' '.join(chunks).strip()
        m = PAGE.match(line)
        if m:
            page, section = int(m.group(1)), ''
            continue
        if page is None or re.fullmatch(r'\d+|Unit \d+|Get Ready|Answer Key', line):
            continue
        m = NUM.match(chunks[0])
        if m:
            # headings are images and a "p. N" label is sometimes missing (JR4 p.17):
            # a repeated item number in the same section means the next page began
            if any(s == section and n == int(m.group(1)) for s, n, _ in data[page]['num']):
                page += 1
            data[page]['num'].append((section, int(m.group(1)), m.group(2).strip()))
            data[page]['free'].extend(chunks[1:])
        elif re.match(r'^(Match|Choose|Complete|Write|Fill|Circle|Read|Look)\b', line) and line.endswith('.'):
            section = line
        else:
            data[page]['free'].extend(chunks)
    return data


def comp_key(q):
    if q['type'] == 'mc':
        return ['abc'[q['answer']]]
    if q['type'] == 'tf':
        return ['true' if q['answer'] else 'false']
    vals = q.get('answers') or [q.get('answer')]
    return [norm(a) for a in vals + q.get('accept', []) if a]


EMPTY = {'num': [], 'free': []}

# Reviewed by hand against the passage; the publisher key is wrong or differs only in wording.
KNOWN = {
    'JR1-U05 C4': 'AK True; passage: "Frogs and toads look different."',
    'JR2-U08 C5': 'AK True; stem says "fun and night", passage: "celebrates fun ... celebrates winter"',
    'JR2-U12 C5': 'AK False, but the official Lv2 Mid-Term test (Q8) says True; passage: "Jackson Haines put a blade on a boot in 1865"',
    'JR2-U14 C5': 'AK False; passage: "Scientists are trying to make new cars to keep the air clean"',
    'JR3-U08 V3': 'AK "drips"; the book word bank prints "dripping" and the blank needs -ing',
    'JR4-U14 O': 'AK image text loses "9.4"; the rendered key shows "9.4 kilometers round"',
    'JR4-U03 O': 'apostrophe glyph split in AK text layer; rendered key matches',
    'JR4-U03 O+': 'same apostrophe artifact',
    'JR1-U05 O+': 'Venn diagram labels (Frogs VS Toads), not answers',
}


def compare(b, ak):
    book = json.load(open(os.path.join(ROOT, 'content', f'book{b}.json')))
    issues = []

    def add(where, mine, theirs, note=''):
        issues.append({'where': where, 'mine': mine, 'ak': theirs, 'note': note})

    for u in book['units']:
        tag, bp = f"JR{b}-U{u['unit']:02d}", u['book_page']
        got = {n: a for _, n, a in ak.get(bp + 2, EMPTY)['num']}
        for q in u['comprehension']:
            a = got.get(q['n'])
            if a is None or not {norm(x) for x in a.split(' / ')} <= set(comp_key(q)):
                add(f'{tag} C{q["n"]}', comp_key(q), a)
        vp = ak.get(bp + 3, EMPTY)
        got = {n: a for _, n, a in vp['num']}
        for it in u['build_vocab']['items']:
            a = got.get(it['n'])
            if a is None or norm(a) != norm(it['answer']):
                add(f'{tag} V{it["n"]}', it['answer'], a)
        # organizer cells wrap and interleave, so compare word sets
        words = set(norm(' '.join(vp['free'])).split())
        rows = u['organizer']['rows']
        for r in rows:
            if r.get('answers') and not any(set(norm(a).split()) <= words for a in r['answers']):
                add(f'{tag} O', r['answers'], vp['free'], 'organizer answer not found in AK')
        mine = set(norm(' '.join(a for r in rows for a in r.get('answers', []))).split())
        extra = [x for x in vp['free'] if norm(x) not in ('', 'unit') and not set(norm(x).split()) <= mine]
        if extra:
            add(f'{tag} O+', None, extra, 'AK organizer text not among my answers')
    for v in book['vocab_checks']:
        tag = f"JR{b}-VC{v['n']}"
        nums, free = [], []
        for p in (v['book_page'], v['book_page'] + 1):
            nums += ak.get(p, EMPTY)['num']
            free += ak.get(p, EMPTY)['free']
        secs = []
        for s, n, a in nums:
            if not secs or secs[-1][0] != s or n in secs[-1][1]:
                secs.append((s, {}))
            secs[-1][1][n] = a
        numbered = [s for s in v['sections'] if s['type'] != 'cloze']
        if len(secs) != len(numbered):
            add(tag, [s['instruction'] for s in numbered], [s for s, _ in secs], 'section count differs')
        for s, (_, got) in zip(numbered, secs):
            for it in s['items']:
                a = got.get(it['n'])
                mine = 'abc'[it['answer']] if s['type'] == 'mc' else 'abcd'[s['options'].index(it['answer'])]
                if a is None or norm(a) != mine:
                    add(f'{tag} {s["type"]} {it["n"]}', mine, a)
        flat = norm(' '.join(free))
        for s in v['sections']:
            if s['type'] == 'cloze':
                for k, a in s['answers'].items():
                    if norm(a) not in flat:
                        add(f'{tag} cloze {k}', a, free, 'cloze answer not found')
    return issues


if __name__ == '__main__':
    d = sys.argv[1]
    report = {}
    for b in (1, 2, 3, 4):
        report[b] = [i for i in compare(b, parse(os.path.join(d, f'ak{b}.pdf'))) if i['where'] not in KNOWN]
        print(f'== Book {b}: {len(report[b])} issue(s)')
        for i in report[b]:
            print('  ', i['where'], '| mine:', i['mine'], '| AK:', i['ak'], '|', i['note'])
    os.makedirs(os.path.join(ROOT, 'build'), exist_ok=True)
    json.dump(report, open(os.path.join(ROOT, 'build', 'ak_report.json'), 'w'), ensure_ascii=False, indent=1)
    print(f'KNOWN: {len(KNOWN)}  MISMATCHES: {sum(map(len, report.values()))}')
    sys.exit(1 if any(report.values()) else 0)
