#!/usr/bin/env python3
"""Standalone DEMO pages (no server): one self-contained HTML file per library item + an index.

    python3 tools/site.py OUT_DIR MEDIA_DIR SITE_DIR

Each page embeds its pictures (data URIs) and its answer key, checks answers in the browser and shows
the score with corrections. Listening: the page plays `audio/jr{b}-u{nn}.mp3` next to it when that file
exists (copy the Telegram tracks there), otherwise it says so. The graded, logged version of the same
material lives on the Turbo English platform.
"""
import base64, html, json, os, sys

CSS = """
:root{--bg:#f3f7fc;--card:#fff;--ink:#172033;--muted:#4b5a72;--line:#d8e3ef;--pri:#2563eb;--pri-d:#1d4ed8;--ok:#15803d;--ok-bg:#ecfdf3;--bad:#b42318;--bad-bg:#fff1f0;--soft:#eff6ff;--warn:#92400e;--warn-bg:#fff8e7}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
.wrap{max-width:860px;margin:0 auto;padding:16px}a{color:var(--pri-d)}
header.top{display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.kicker{font-size:12px;font-weight:700;letter-spacing:.08em;color:var(--muted);text-transform:uppercase}
h1{font-size:26px;margin:4px 0 12px}h2{font-size:20px;margin:28px 0 8px}h3{font-size:17px;margin:18px 0 6px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;margin:12px 0}
.hero{width:100%;border-radius:14px;display:block;border:1px solid var(--line)}
.words{list-style:none;padding:0;margin:8px 0;display:flex;flex-wrap:wrap;gap:8px}
.words li{background:var(--soft);border:1px solid #bfdbfe;border-radius:12px;padding:8px 12px;display:flex;flex-direction:column;line-height:1.25}
.words b{color:var(--pri-d);font-size:18px}.words span{color:var(--muted);font-size:14px}
.passage p{margin:0 0 12px;font-size:18px;line-height:1.75}
.bank{list-style:none;padding:0;margin:6px 0 10px;display:flex;flex-wrap:wrap;gap:8px}.bank li{border:1px dashed #b4c4d8;border-radius:999px;padding:4px 12px;font-weight:600;background:#fff}
.task{font-weight:700;margin:12px 0 4px}
fieldset.q{border:1px solid var(--line);border-radius:12px;margin:10px 0;padding:12px 14px;background:#fff}
fieldset.q legend{float:left;width:100%;padding:0;margin:0 0 8px;font-weight:600}fieldset.q legend+*{clear:both}.q .num{display:inline-block;min-width:26px;height:26px;border-radius:50%;background:var(--pri);color:#fff;text-align:center;font-size:14px;line-height:26px;margin-right:6px}
.opt{display:flex;align-items:center;gap:10px;min-height:44px;padding:6px 10px;border:1px solid var(--line);border-radius:10px;margin:6px 0;cursor:pointer}
.opt input{width:20px;height:20px}.q input[type=text]{width:100%;min-height:44px;font:inherit;padding:8px 10px;border:1px solid #b4c4d8;border-radius:10px}
.qimg{max-width:100%;max-height:260px;border-radius:10px;border:1px solid var(--line);margin:6px 0}
.q.is-ok{border-color:var(--ok);background:var(--ok-bg)}.q.is-bad{border-color:var(--bad);background:var(--bad-bg)}
.fb{margin-top:6px;font-weight:600}.is-ok .fb{color:var(--ok)}.is-bad .fb{color:var(--bad)}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:10px 18px;border-radius:12px;border:1px solid var(--pri);background:var(--pri);color:#fff;font:inherit;font-weight:700;cursor:pointer;text-decoration:none}
.btn.ghost{background:#fff;color:var(--pri-d)}.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.score{font-size:40px;font-weight:800}.note{background:var(--warn-bg);border:1px solid #f3d79a;color:var(--warn);border-radius:12px;padding:10px 12px}
audio{width:100%}details summary{cursor:pointer;font-weight:700;min-height:44px;display:flex;align-items:center}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px}
.unit{display:block;background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px;text-decoration:none;color:var(--ink)}
.unit b{display:block}.unit span{color:var(--muted);font-size:14px}.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0 14px}
.tabs a{padding:8px 14px;border-radius:999px;border:1px solid var(--line);background:#fff;text-decoration:none;color:var(--ink);font-weight:600}
@media (max-width:520px){h1{font-size:22px}.passage p{font-size:17px}}
"""

JS = r"""
(function(){
  var D = JSON.parse(document.getElementById('data').textContent);
  var norm = function(v){return String(v||'').toLowerCase().replace(/[’‘ʻʼ`]/g,"'").replace(/[.,!?;:()\[\]{}"]/g,' ').replace(/\s+/g,' ').trim();};
  function textOk(r, acc){ r = norm(r); if(!r) return false;
    return acc.some(function(raw){ var a = norm(raw); if(!a) return false; if(r===a) return true;
      var rt = r.split(' '), at = a.split(' '), hit = at.filter(function(x){return rt.indexOf(x)>=0;}).length;
      return hit/at.length >= 0.9 && rt.length/at.length >= 0.7; }); }
  var form = document.getElementById('paper'), out = document.getElementById('result');
  var KEY = 'jr-draft-' + D.code;
  try { var saved = JSON.parse(localStorage.getItem(KEY) || 'null'); if (saved) Object.keys(saved).forEach(function(n){ var els = form.elements[n]; if(!els) return;
      if (els.length && els[0] && els[0].type === 'radio') { [].forEach.call(els, function(e){ e.checked = e.value === saved[n]; }); } else if (els.type === 'text') els.value = saved[n]; }); } catch(e) {}
  form.addEventListener('input', function(){ try { var o = {}; D.q.forEach(function(q){ var el = form.elements[q.id]; if (!el) return; o[q.id] = el.value || ''; }); localStorage.setItem(KEY, JSON.stringify(o)); } catch(e) {} });
  form.addEventListener('submit', function(ev){
    ev.preventDefault();
    var ok = 0;
    D.q.forEach(function(q, i){
      var fs = document.getElementById('f-' + q.id), fb = fs.querySelector('.fb'), right;
      if (q.t) { var v = form.elements[q.id].value; right = textOk(v, q.t); fb.textContent = right ? 'To‘g‘ri!' : 'To‘g‘ri javob: ' + q.t[0]; }
      else { var el = form.querySelector('input[name="' + q.id + '"]:checked'); right = !!el && Number(el.value) === q.a; fb.textContent = right ? 'To‘g‘ri!' : 'To‘g‘ri javob: ' + q.o[q.a]; }
      fs.classList.toggle('is-ok', right); fs.classList.toggle('is-bad', !right); if (right) ok++;
    });
    var pct = Math.round(100 * ok / D.q.length);
    out.hidden = false;
    out.innerHTML = '<div class="kicker">NATIJA</div><div class="score">' + ok + ' / ' + D.q.length + ' · ' + pct + '%</div><p>' + (pct >= 80 ? 'Barakalla! Juda yaxshi.' : pct >= 50 ? 'Yaxshi. Xatolarni ko‘rib chiqing va qayta urinib ko‘ring.' : 'Matnni yana bir marta o‘qing va qayta urinib ko‘ring.') + '</p><button type="button" class="btn ghost" id="again">Qayta boshlash</button>';
    document.getElementById('again').onclick = function(){ form.reset(); try { localStorage.removeItem(KEY); } catch(e) {} document.querySelectorAll('.q').forEach(function(f){ f.classList.remove('is-ok','is-bad'); f.querySelector('.fb').textContent=''; }); out.hidden = true; window.scrollTo(0, form.offsetTop - 20); };
    out.scrollIntoView({behavior:'smooth', block:'center'});
  });
  var au = document.getElementById('track');
  if (au) au.addEventListener('error', function(){ var n = document.getElementById('trackNote'); if (n) n.hidden = false; au.hidden = true; });
})();
"""


def e(s):
    return html.escape(str(s), quote=True)


def rich(s):
    # the content uses only <b>/<i>/<u> in stems (organizer labels); everything else is escaped
    out = e(s)
    for t in ('b', 'i', 'u'):
        out = out.replace(f'&lt;{t}&gt;', f'<{t}>').replace(f'&lt;/{t}&gt;', f'</{t}>')
    return out


def img(media_dir, mid, cls, alt):
    p = os.path.join(media_dir, mid + '.jpg')
    if not os.path.exists(p):
        return ''
    return f'<img class="{cls}" alt="{e(alt)}" src="data:image/jpeg;base64,{base64.b64encode(open(p, "rb").read()).decode()}">'


def page(r, media_dir, prev_next):
    c, key = r['content'], r['answer_key']['items']
    j = c.get('juice', {})
    parts = [f'<header class="top"><a href="index.html#b{r["book"]}">← Reading Juice {r["book"]}</a><span class="row">{prev_next}</span></header>',
             f'<div class="kicker">Reading Juice for Kids {r["book"]} · {e(j.get("subject") or "Vocabulary Check")}</div><h1>{e(r["title"].split(" — ")[-1] if " — " in r["title"] else r["title"].split(" · ", 1)[-1])}</h1>']
    if c.get('image'):
        parts.append(img(media_dir, c['image'], 'hero', r['title']))
    if c.get('audio'):
        f = c['audio'].replace('/', '-') + '.mp3'
        parts.append(f'<div class="card"><b>🎧 Audio — matnni tinglang</b><audio id="track" controls preload="metadata" src="audio/{e(f)}"></audio>'
                     f'<p class="note" id="trackNote" hidden>Audio fayl topilmadi: <code>audio/{e(f)}</code>. Telegram kanaldagi yozuvni shu nom bilan <code>audio</code> papkasiga qo‘ying.</p></div>')
    if c.get('words'):
        parts.append('<h2>Yangi so‘zlar · Listen and repeat</h2><ul class="words">' + ''.join(
            f'<li title="{e(w.get("d", ""))}"><b lang="en">{e(w["w"])}</b><span>{e(w.get("uz", ""))}</span></li>' for w in c['words']) + '</ul>')
    w = c.get('warmup')
    if w:
        body = (f'<p class="task">{e(w.get("prompt", ""))}</p>' + ('<ul class="bank">' + ''.join(f'<li>{e(x)}</li>' for x in w.get('bank', [])) + '</ul>' if w.get('bank') else '')
                + ('<ul>' + ''.join(f'<li>{rich(x)}</li>' for x in w.get('items', [])) + '</ul>' if w.get('items') else '')
                + ('<p class="task">Listen and repeat the sentences.</p><ul>' + ''.join(f'<li>{e(x)}</li>' for x in w['sentences']) + '</ul>' if w.get('sentences') else ''))
        parts.append(f'<details class="card"><summary>Get Ready — o‘qishdan oldin o‘ylab ko‘ring</summary>{body}</details>')
    if c.get('passage'):
        title = 'Matn' if r['kind'] == 'unit' else 'Dialog'
        parts.append(f'<h2>{title}</h2><div class="card passage">' + ''.join(f'<p>{e(p)}</p>' for p in c['passage'].split('\n\n') if p.strip()).replace('\n', '<br>') + '</div>')
    qs, data, prev = c['questions'], [], {}
    body = []
    for i, q in enumerate(qs, 1):
        if q.get('section') != prev.get('section'):
            body.append(f'<h2>{e(q["section"])}</h2>')
        if q.get('task') and (q.get('task') != prev.get('task') or q.get('section') != prev.get('section')):
            body.append(f'<p class="task">{e(q["task"])}</p>')
        if q.get('bank') and (q.get('bank') != prev.get('bank') or q.get('section') != prev.get('section')):
            body.append('<ul class="bank">' + ''.join(f'<li>{e(x)}</li>' for x in q['bank']) + '</ul>')
        prev = q
        k = key[q['id']]
        pic = img(media_dir, q['img'], 'qimg', f'{i}-savol rasmi') if q.get('img') else ''
        if q.get('type') == 'text':
            inp = f'<input type="text" name="{e(q["id"])}" autocomplete="off" autocapitalize="none" spellcheck="false" aria-label="{i}-savol javobi">'
            data.append({'id': q['id'], 't': k['t']})
        else:
            inp = ''.join(f'<label class="opt"><input type="radio" name="{e(q["id"])}" value="{j2}"><span>{rich(o)}</span></label>' for j2, o in enumerate(q['options']))
            data.append({'id': q['id'], 'a': k['a'], 'o': q['options']})
        body.append(f'<fieldset class="q" id="f-{e(q["id"])}"><legend><span class="num">{i}</span>{rich(q["q"])}</legend>{pic}{inp}<div class="fb" aria-live="polite"></div></fieldset>')
    parts.append('<form id="paper" novalidate>' + ''.join(body) + '<div class="row" style="margin:16px 0"><button class="btn" type="submit">Tekshirish</button></div></form><div class="card" id="result" hidden aria-live="polite"></div>')
    payload = json.dumps({'code': r['code'], 'q': data}, ensure_ascii=False).replace('</', '<\\/')
    return (f'<!doctype html><html lang="uz"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(r["title"])}</title><style>{CSS}</style></head><body><main class="wrap">{"".join(parts)}</main>'
            f'<script type="application/json" id="data">{payload}</script><script>{JS}</script></body></html>')


def main(out_dir, media_dir, site_dir):
    os.makedirs(os.path.join(site_dir, 'audio'), exist_ok=True)
    rows = [json.load(open(os.path.join(out_dir, 'units', f))) for f in sorted(os.listdir(os.path.join(out_dir, 'units'))) if f.endswith('.json')]
    rows.sort(key=lambda r: (r['book'], r['sort']))
    name = lambda r: r['code'].lower() + '.html'
    for i, r in enumerate(rows):
        same = [x for x in rows if x['book'] == r['book']]
        k = same.index(r)
        nav = (f'<a class="btn ghost" href="{name(same[k - 1])}">←</a>' if k else '') + (f'<a class="btn ghost" href="{name(same[k + 1])}">→</a>' if k + 1 < len(same) else '')
        open(os.path.join(site_dir, name(r)), 'w').write(page(r, media_dir, nav))
    idx = ['<header class="top"><div><div class="kicker">3-SINF · INGLIZ TILI</div><h1>Reading Juice for Kids 1–4</h1></div></header>',
           '<p>Har bir unit: rasm, audio, yangi so‘zlar (o‘zbekcha tarjimasi bilan), matn va avtomatik tekshiriladigan savollar. Har 4 unitdan keyin — Vocabulary Check.</p>',
           '<nav class="tabs">' + ''.join(f'<a href="#b{b}">Reading Juice {b}</a>' for b in (1, 2, 3, 4)) + '</nav>']
    for b in (1, 2, 3, 4):
        items = [r for r in rows if r['book'] == b]
        if not items:
            continue
        idx.append(f'<h2 id="b{b}">Reading Juice {b}</h2><div class="grid">' + ''.join(
            f'<a class="unit" href="{name(r)}"><b>{e(r["title"].split(" · ", 1)[1])}</b><span>{r["items"]} ta savol</span></a>' for r in items) + '</div>')
    open(os.path.join(site_dir, 'index.html'), 'w').write(
        f'<!doctype html><html lang="uz"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Reading Juice for Kids</title><style>{CSS}</style></head><body><main class="wrap">{"".join(idx)}</main></body></html>')
    open(os.path.join(site_dir, 'audio', 'README.txt'), 'w').write(
        'Telegram kanaldagi audiolarni shu papkaga quyidagi nomlar bilan qo‘ying:\n  jr1-u01.mp3 … jr1-u16.mp3, jr2-u01.mp3 … jr4-u16.mp3\n(jr<kitob>-u<unit, ikki xonali>.mp3). Sahifa audioni o‘zi topadi.\n')
    print(f'{len(rows)} pages + index → {site_dir}')


if __name__ == '__main__':
    main(*sys.argv[1:4])
