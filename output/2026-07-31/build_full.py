# -*- coding: utf-8 -*-
"""②完全版マニュアルのHTMLを①DBから生成する。

  python output/2026-07-31/build_full.py

structure.py の章節構成に従って組む。事実・数値・固有名詞・手順・セリフは
DBのとおりで変更しない。図表は「別シート（ID○○）」のB1の表示形式に従い、
「内容」列の中の ｜区切り・①②③ は表・番号付きリストとして組む
（HTML版マニュアル web/index.html と同じ規則）。

対象行とstructure.pyのIDが食い違っていたら生成せず中断する。
"""
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os, re, sys, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from structure import SECTIONS

SA = os.path.expanduser('~/.sasho/service-account.json')
DB = '1VxEepC6PHtTO_Ic1JckaKMP9lItFCqhLLc5cpE2Gkkk'
HERE = os.path.dirname(os.path.abspath(__file__))
RE_SHEET = re.compile(r'^ID\d+$')
GENRES = ["開店・閉店作業", "メニュー・料金", "ドリンク", "客席・レイアウト",
          "オペレーション・接客", "清掃・衛生", "備品・在庫", "発注・仕入れ",
          "設備・機器", "安全管理", "予約・レジ", "調理・仕込み", "身だしなみ"]

STEP = re.compile(r'^(?:[①-⑳]|\d{1,2}[.．])\s*')
SPEAKER = re.compile(r'^([^：:「」]{1,24})[：:]\s*[「]')
NGOK = re.compile(r'^[　\s]*(NG例|OK例|NG|OK)[：:]\s*(.*)$')
TODO = '【要確認】'   # 内部マーカー。②③には出さない（→ 備考列と同じ扱い）
DROPPED = []        # 出力から落とした【要確認】の記録


# ────────────────────────── 読み込み ──────────────────────────
def load():
    creds = service_account.Credentials.from_service_account_file(
        SA, scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
    svc = build('sheets', 'v4', credentials=creds)

    meta = svc.spreadsheets().get(spreadsheetId=DB).execute()
    names = [s['properties']['title'] for s in meta['sheets']
             if RE_SHEET.match(s['properties']['title'])]

    sheets = {}
    for name in names:
        vals = svc.spreadsheets().values().get(
            spreadsheetId=DB, range=f"'{name}'!A1:H300").execute().get('values', [])
        if not vals:
            continue
        kind = (vals[0][1].strip() if len(vals[0]) > 1 else '')
        if kind == 'チェックリスト':
            sheets[name] = {'kind': kind,
                            'items': [str(r[1]).strip() for r in vals[2:]
                                      if len(r) >= 2 and str(r[0]).strip() and str(r[1]).strip()]}
        else:
            body = vals[1:] if kind in ('表', '対応表') else vals[2:]
            rows = []
            for r in body:
                c = [str(r[i]).strip() if i < len(r) else '' for i in range(6)]
                while c and not c[-1]:
                    c.pop()
                if c:
                    rows.append(c)
            sheets[name] = {'kind': kind, 'rows': rows}

    hdr = svc.spreadsheets().values().get(
        spreadsheetId=DB, range="マニュアルDB!A1:Q1").execute()['values'][0]
    raw = svc.spreadsheets().values().get(
        spreadsheetId=DB, range="マニュアルDB!A2:Q400").execute().get('values', [])

    items = {}
    for r in raw:
        if not r or not r[0]:
            continue
        d = {h: (r[i] if i < len(r) else '') for i, h in enumerate(hdr)}
        if d['ステータス'] != '有効' or str(d['清書完了']).upper() != 'TRUE':
            continue
        items[int(d['ID'])] = d
    return items, sheets


# ────────────────────────── 本文の組み立て ──────────────────────────
def esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def is_num(s):
    s = (s or "").strip()
    return bool(re.match(r'^[¥￥$]?[\d,]+(\.\d+)?$', s) or re.match(r'^[+\-][¥￥$]?[\d,]', s))


def inline(t):
    """1行の中の強調だけ処理する。**〜** を太字に。"""
    return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', esc(t))


def ngok_box(kind, text):
    cls = 'ng' if kind.startswith('NG') else 'ok'
    return f'<div class="{cls}"><span class="lbl">{esc(kind)}</span>{inline(text)}</div>'


def num_cols(head, body):
    """列内の値が全て数値の列だけ右寄せにする。"""
    out = set()
    for i in range(1, len(head)):
        vals = [r[i] for r in body if i < len(r) and r[i]]
        if vals and all(is_num(v) for v in vals):
            out.add(i)
    return out


def bar_table(lines):
    cells = [[c.strip() for c in l.split('｜')] for l in lines]
    n = max(len(r) for r in cells)
    nc = num_cols([''] * n, cells[1:])
    h = ['<table class="fg"><thead><tr>']
    for i in range(n):
        h.append('<th>' + inline(cells[0][i] if i < len(cells[0]) else '') + '</th>')
    h.append('</tr></thead><tbody>')
    for r in cells[1:]:
        h.append('<tr>')
        for i in range(n):
            v = r[i] if i < len(r) else ''
            h.append(f'<td{" class=\"num\"" if i in nc else ""}>{inline(v)}</td>')
        h.append('</tr>')
    h.append('</tbody></table>')
    return ''.join(h)


def steps(lines):
    """①②③ / 1. 2. 3. の手順。全角スペース始まりの行は直前の手順の続き。"""
    out, cur = [], None
    for l in lines:
        if STEP.match(l.strip()) and not l.startswith('　'):
            if cur:
                out.append(cur)
            cur = [STEP.sub('', l.strip()), []]
        elif cur is not None:
            cur[1].append(l.strip())
    if cur:
        out.append(cur)
    h = ['<ol class="steps">']
    for head, tail in out:
        h.append('<li>' + inline(head))
        for t in tail:
            m = NGOK.match(t)
            h.append(ngok_box(m.group(1), m.group(2)) if m else '<div class="sub">' + inline(t) + '</div>')
        h.append('</li>')
    h.append('</ol>')
    return ''.join(h)


def talk(lines):
    h = ['<div class="talk">']
    for l in lines:
        t = l.strip()
        mm = NGOK.match(t)          # 「NG例：「〜」」は話者ではないので先に判定する
        if mm:
            h.append(ngok_box(mm.group(1), mm.group(2)))
            continue
        m = SPEAKER.match(t)
        if m:
            who = m.group(1)
            h.append(f'<div class="ln"><span class="who">{esc(who)}</span>'
                     f'<span class="say">{inline(t[len(who) + 1:].strip())}</span></div>')
        else:
            h.append('<div class="note2">' + inline(t) + '</div>')
    h.append('</div>')
    return ''.join(h)


def body_html(text, _id=None):
    out = []
    for para in re.split(r'\n{2,}', (text or '').strip()):
        ls = [l for l in para.split('\n') if l.strip()]
        # 【要確認】は内部メモ。成果物には出さず、記録して報告する
        for l in ls:
            if TODO in l:
                DROPPED.append((_id, l.strip()))
        ls = [l for l in ls if TODO not in l]
        if not ls:
            continue
        bars = [l for l in ls if '｜' in l]
        heads = [l for l in ls if STEP.match(l.strip()) and not l.startswith('　')]
        talks = [l for l in ls if SPEAKER.match(l.strip())]

        if len(bars) == len(ls) and len(ls) >= 2:
            out.append(bar_table(ls))
        elif len(heads) >= 2:
            out.append(steps(ls))
        elif len(talks) >= 2:
            out.append(talk(ls))
        elif all(l.strip().startswith(('・', '‐', '-')) for l in ls):
            out.append('<ul class="bl">' + ''.join(
                '<li>' + inline(re.sub(r'^[・‐\-]\s*', '', l.strip())) + '</li>' for l in ls) + '</ul>')
        elif para.strip().startswith('【'):
            out.append('<div class="note">' + '<br>'.join(inline(l) for l in ls) + '</div>')
        else:
            buf, note = [], None
            def flush():
                if buf:
                    out.append('<p>' + '<br>'.join(buf) + '</p>')
                    buf.clear()
            for l in ls:
                t = l.strip()
                if note is not None:          # 【背景】以降はそのまま補足ボックスに入れる
                    note.append(t)
                    continue
                if t.startswith('【'):
                    flush()
                    note = [t]
                    continue
                m = NGOK.match(l)
                if m:
                    flush()
                    out.append(ngok_box(m.group(1), m.group(2)))
                elif t.startswith('※'):
                    flush()
                    out.append('<div class="note2">' + inline(t) + '</div>')
                else:
                    buf.append(inline(l))
            flush()
            if note:
                head, rest = note[0], note[1:]
                h = ['<div class="note">', inline(head)]
                bl = [x for x in rest if x.startswith(('・', '‐', '-'))]
                if bl and len(bl) == len(rest):
                    h.append('<ul class="bl">' + ''.join(
                        '<li>' + inline(re.sub(r'^[・‐\-]\s*', '', x)) + '</li>' for x in rest) + '</ul>')
                elif rest:
                    h.append('<br>' + '<br>'.join(inline(x) for x in rest))
                h.append('</div>')
                out.append(''.join(h))
    return ''.join(out)


# ────────────────────────── 図表（別シート） ──────────────────────────
def figure(kind, rows):
    if not rows:
        return ''
    if kind in ('表', '対応表'):
        head, body = rows[0], rows[1:]
        nc = num_cols(head, body)
        h = ['<table class="fg"><thead><tr>']
        h += ['<th>' + inline(c) + '</th>' for c in head]
        h.append('</tr></thead><tbody>')
        for r in body:
            h.append('<tr>')
            for i in range(len(head)):
                v = r[i] if i < len(r) else ''
                h.append(f'<td{" class=\"num\"" if i in nc else ""}>{inline(v)}</td>')
            h.append('</tr>')
        h.append('</tbody></table>')
        return ''.join(h)

    if kind == '配置図':
        groups = []
        for r in rows:
            g, pos, val = (r + ['', '', ''])[:3]
            if not groups or groups[-1][0] != g:
                groups.append((g, []))
            groups[-1][1].append((pos, val))
        h = ['<div class="shelf">']
        for g, cells in groups:
            h.append(f'<div class="col"><div class="cap">{esc(g)}</div>')
            for pos, val in cells:
                h.append('<div class="cell">'
                         + (f'<small>{esc(pos)}</small>' if pos else '')
                         + inline(val) + '</div>')
            h.append('</div>')
        h.append('</div>')
        return ''.join(h)

    if kind == '色見本':
        h = ['<table class="fg sw-t"><thead><tr><th>色</th><th>用途</th></tr></thead><tbody>']
        for r in rows:
            r = (r + ['', '', ''])[:3]
            sw = (f'<span class="sw" style="background:{esc(r[1])}"></span>'
                  if re.match(r'^#[0-9a-fA-F]{3,8}$', r[1]) else '')
            h.append(f'<td class="cn">{sw}{inline(r[0])}</td><td>{inline(r[2])}</td></tr>')
        return ''.join(h).replace('<td class="cn">', '<tr><td class="cn">') + '</tbody></table>'

    if kind == '対比':
        groups = []
        for r in rows:
            k, v = (r + ['', ''])[:2]
            if not groups or groups[-1][0] != k:
                groups.append((k, []))
            groups[-1][1].append(v)
        h = ['<div class="cmp">']
        for k, vs in groups:
            h.append(f'<div class="col"><div class="ch2">{esc(k)}</div><ul>')
            h += ['<li>' + inline(v) + '</li>' for v in vs]
            h.append('</ul></div>')
        h.append('</div>')
        return ''.join(h)

    if kind == 'タイムライン':
        h = ['<div class="tl">']
        for r in rows:
            r = (r + ['', '', ''])[:3]
            h.append(f'<div class="row"><div class="tm">{inline(r[0])}</div>'
                     f'<div class="ev">{inline(r[1])}'
                     + (f'<small>{inline(r[2])}</small>' if r[2] else '') + '</div></div>')
        h.append('</div>')
        return ''.join(h)

    if kind == '手順':
        return '<ol class="steps">' + ''.join('<li>' + inline(r[0]) + '</li>' for r in rows) + '</ol>'

    # 表示形式が想定外のときも情報を落とさない
    h = ['<table class="fg"><tbody>']
    for r in rows:
        h.append('<tr>' + ''.join('<td>' + inline(c) + '</td>' for c in r) + '</tr>')
    h.append('</tbody></table>')
    return ''.join(h)


def checklist(items):
    return '<ol class="cl">' + ''.join('<li>' + inline(x) + '</li>' for x in items) + '</ol>'


# ────────────────────────── 組版 ──────────────────────────
def render(items, sheets, today):
    # 網羅チェック
    planned = [i for _, secs in SECTIONS.values() for _, _, ids in secs for i in ids]
    dup = sorted({i for i in planned if planned.count(i) > 1})
    missing = sorted(set(items) - set(planned))
    extra = sorted(set(planned) - set(items))
    if dup or missing or extra:
        print("!! structure.py と対象行が一致しません。生成を中断します。")
        if dup:     print("   重複:", dup)
        if missing: print("   構成に無い対象ID:", missing)
        if extra:   print("   対象外なのに構成にあるID:", extra)
        sys.exit(1)
    for g, (_, secs) in SECTIONS.items():
        for _, name, ids in secs:
            for i in ids:
                if items[i]['大ジャンル'].strip() != g:
                    print(f"!! ID{i} は「{items[i]['大ジャンル']}」だが「{g}」の {name} に置かれています")
                    sys.exit(1)

    chapters = [g for g in GENRES if g in SECTIONS and
                any(ids for _, _, ids in SECTIONS[g][1])]

    h = []
    ymd = datetime.date.fromisoformat(today)
    jp = f"{ymd.year}年{ymd.month}月{ymd.day}日"

    # 表紙
    h.append(f'''<section class="cover">
  <div class="ctop">Sasho</div>
  <h1 class="ctitle">マニュアル</h1>
  <div class="csub">完全版</div>
  <div class="crule"></div>
  <div class="cdate">{jp}</div>
  <div class="cnote">このPDFは{jp}にマニュアルDBから自動生成されました。<br>
    修正・追加の要望は経営陣へ。</div>
</section>''')

    # 目次
    h.append('<section class="toc"><h2 class="pg-h">目次</h2><div class="toc-g">')
    for n, g in enumerate(chapters, 1):
        lead, secs = SECTIONS[g]
        cnt = sum(len(ids) for _, _, ids in secs)
        h.append(f'<div class="toc-ch"><a href="#ch{n}"><span class="tn">第{n}章</span>'
                 f'<span class="tt">{esc(g)}</span><span class="tc">{cnt}項目</span></a><ul>')
        for num, name, ids in secs:
            if ids:
                h.append(f'<li><a href="#s{num}">{esc(num)}　{esc(name)}</a></li>')
        h.append('</ul></div>')
    h.append('</div></section>')

    # 本文
    for n, g in enumerate(chapters, 1):
        lead, secs = SECTIONS[g]
        h.append(f'<section class="ch" id="ch{n}">')
        h.append(f'<h1 class="ch-h"><span class="ch-n">第{n}章</span>'
                 f'<span class="ch-t">{esc(g)}</span></h1>')
        h.append(f'<p class="ch-ld">{inline(lead)}</p>')
        h.append('<div class="ch-mp">' + ''.join(
            f'<span>{esc(num)} {esc(name)}</span>' for num, name, ids in secs if ids) + '</div>')

        for num, name, ids in secs:
            if not ids:
                continue
            h.append(f'<h2 class="sec-h" id="s{num}"><span class="sec-n">{esc(num)}</span>'
                     f'<span class="sec-t">{esc(name)}</span></h2>')
            for i in ids:
                d = items[i]
                sh0 = d['別シート'].strip()
                n_cl = len(sheets.get(sh0, {}).get('items', []) or [])
                cls = ('it' + (' safety' if g == '安全管理' else '')
                       + (' long' if n_cl >= 8 or len(d['内容']) > 320 else ''))
                h.append(f'<div class="{cls}"><h3 class="it-h"><span>{esc(d["タイトル"])}</span>'
                         f'<span class="id">ID {i}</span></h3>')
                h.append(body_html(d['内容'], i))
                sh = d['別シート'].strip()
                if sh in sheets:
                    s = sheets[sh]
                    h.append(checklist(s['items']) if s['kind'] == 'チェックリスト'
                             else figure(s['kind'], s['rows']))
                h.append('</div>')
        h.append('</section>')

    return CSS_HEAD + ''.join(h) + '</body></html>'


CSS_HEAD = '''<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8"><title>Sasho マニュアル 完全版</title>
<style>
@page { size: A4 portrait; margin: 17mm 15mm 16mm; }
:root{
  --ink:#1a1a1a; --ink2:#41474d; --ink3:#7d858c;
  --accent:#2b4257; --accent-l:#edf1f4; --accent-b:#c0ccd6;
  --ng:#9c3428; --ng-bg:#fbf1ef; --ok:#2f6b4f; --ok-bg:#eff5f1;
  --warn:#8a6521; --warn-bg:#fbf6ea; --line:#dfe4e8; --paper:#f7f8f9;
  --mincho:"Hiragino Mincho ProN","Yu Mincho","YuMincho",serif;
  --gothic:"Hiragino Sans","Yu Gothic Medium","Yu Gothic","Meiryo",sans-serif;
}
*{box-sizing:border-box}
body{margin:0;font-family:var(--gothic);color:var(--ink);
  font-size:10.4pt;line-height:1.85;-webkit-print-color-adjust:exact;print-color-adjust:exact}
p{margin:0 0 6pt}
b{color:var(--accent)}

/* 表紙 */
.cover{height:250mm;display:flex;flex-direction:column;align-items:center;
  justify-content:center;text-align:center;page-break-after:always}
.cover .ctop{font-family:var(--mincho);font-size:13pt;letter-spacing:.5em;
  color:var(--accent);margin-bottom:14mm;padding-left:.5em}
.cover .ctitle{font-family:var(--mincho);font-size:31pt;font-weight:400;
  letter-spacing:.34em;margin:0;padding-left:.34em}
.cover .csub{font-family:var(--mincho);font-size:12pt;letter-spacing:.32em;
  color:var(--ink2);margin-top:5mm;padding-left:.32em}
.cover .crule{width:26mm;height:1.6pt;background:var(--accent);margin:12mm 0}
.cover .cdate{font-family:var(--mincho);font-size:10pt;letter-spacing:.12em;color:var(--ink2)}
.cover .cnote{margin-top:26mm;font-size:8.2pt;line-height:1.9;color:var(--ink3)}

/* 目次 */
.toc{page-break-after:always}
.pg-h{font-family:var(--mincho);font-size:15pt;font-weight:400;letter-spacing:.3em;
  color:var(--accent);margin:0 0 6mm;padding-bottom:2.6mm;
  border-bottom:1.6pt solid var(--accent);padding-left:.3em}
.toc-g{column-count:2;column-gap:9mm}
.toc-ch{break-inside:avoid;margin-bottom:4mm}
.toc-ch>a{display:flex;align-items:baseline;gap:2mm;text-decoration:none;color:inherit;
  border-bottom:.7pt solid var(--accent-b);padding-bottom:1.2mm}
.toc-ch .tn{font-family:var(--mincho);font-size:7.6pt;color:#fff;background:var(--accent);
  padding:.6mm 1.4mm;border-radius:1pt;flex:0 0 auto}
.toc-ch .tt{font-family:var(--mincho);font-size:11pt;font-weight:600}
.toc-ch .tc{margin-left:auto;font-size:7.6pt;color:var(--ink3);flex:0 0 auto}
.toc-ch ul{list-style:none;margin:1.8mm 0 0;padding:0 0 0 1mm}
.toc-ch li{font-size:8.5pt;line-height:1.6;color:var(--ink2)}
.toc-ch li a{text-decoration:none;color:inherit}

/* 章・節 */
.ch{page-break-before:always}
.ch-h{display:flex;align-items:baseline;gap:3mm;margin:0 0 4mm;padding-bottom:2.4mm;
  border-bottom:2pt solid var(--accent)}
.ch-n{font-family:var(--mincho);font-size:8pt;letter-spacing:.1em;color:#fff;
  background:var(--accent);padding:.9mm 2mm;border-radius:1pt;flex:0 0 auto}
.ch-t{font-family:var(--mincho);font-size:17pt;font-weight:600;letter-spacing:.1em}
.ch-ld{font-size:9.8pt;line-height:1.9;color:var(--ink2);margin:0 0 3mm}
.ch-mp{display:flex;flex-wrap:wrap;gap:1.4mm;margin-bottom:6mm}
.ch-mp span{font-size:8.4pt;color:var(--accent);background:var(--accent-l);
  border:.6pt solid var(--accent-b);border-radius:1.4pt;padding:.9mm 2mm}
.sec-h{display:flex;align-items:baseline;gap:2.4mm;margin:7mm 0 3mm;
  page-break-after:avoid;break-after:avoid}
.sec-n{font-family:var(--mincho);font-size:9.4pt;color:var(--accent);flex:0 0 auto;
  border-right:1pt solid var(--accent-b);padding-right:2.4mm}
.sec-t{font-family:var(--mincho);font-size:12.4pt;font-weight:600;letter-spacing:.05em}

/* 項目カード */
.it.long{page-break-inside:auto;break-inside:auto}
.it{border:.7pt solid var(--line);border-left:2.4pt solid var(--accent-b);
  border-radius:0 2pt 2pt 0;padding:3.6mm 4.4mm;margin-bottom:3.6mm;
  page-break-inside:avoid;break-inside:avoid}
.it.safety{border-left-color:var(--warn);background:#fffdf8}
.it-h{display:flex;align-items:baseline;gap:2mm;font-size:11.2pt;font-weight:700;
  margin:0 0 2.4mm;line-height:1.5}
.it-h .id{margin-left:auto;flex:0 0 auto;font-size:7pt;font-weight:400;color:var(--ink3);
  font-variant-numeric:tabular-nums}
.note{background:var(--paper);border-left:2pt solid var(--accent-b);
  padding:2.2mm 3.2mm;margin:2.2mm 0 0;font-size:9.4pt;line-height:1.85;color:var(--ink2)}
.note2{font-size:9.2pt;color:var(--ink2);margin:1.4mm 0 0;padding-left:1em;text-indent:-1em}

/* NG / OK */
.ng,.ok{border-radius:1.6pt;padding:2mm 2.8mm;margin:1.8mm 0 0;font-size:9.4pt;line-height:1.75}
.ng{background:var(--ng-bg);border:.6pt solid #e6cdc8}
.ok{background:var(--ok-bg);border:.6pt solid #cbdfd3}
.ng .lbl,.ok .lbl{display:inline-block;font-size:7pt;font-weight:700;color:#fff;
  border-radius:1pt;padding:.4mm 1.4mm;margin-right:1.8mm;vertical-align:.4mm}
.ng .lbl{background:var(--ng)} .ok .lbl{background:var(--ok)}

/* リスト */
ol.steps,ol.cl{list-style:none;counter-reset:c;margin:2mm 0 0;padding:0}
ol.steps li,ol.cl li{counter-increment:c;position:relative;padding:0 0 1.8mm 6.2mm;
  line-height:1.72}
ol.steps li:last-child,ol.cl li:last-child{padding-bottom:0}
ol.steps li::before,ol.cl li::before{content:counter(c);position:absolute;left:0;top:.4mm;
  width:4.3mm;height:4.3mm;border-radius:50%;background:var(--accent);color:#fff;
  font-size:6.8pt;font-weight:700;text-align:center;line-height:4.3mm}
ol.steps .sub{font-size:9.4pt;color:var(--ink2);margin-top:.8mm}
ul.bl{margin:1.6mm 0 0;padding-left:4.4mm}
ul.bl li{line-height:1.75;padding-bottom:1mm}

/* 会話 */
.talk{margin:2mm 0 0;border-left:2pt solid var(--accent-l);padding-left:3mm}
.talk .ln{display:flex;gap:2.4mm;margin-bottom:1.8mm;font-size:9.6pt;line-height:1.75}
.talk .who{flex:0 0 28mm;font-size:8.6pt;font-weight:700;color:var(--accent);
  background:var(--accent-l);border-radius:1.2pt;padding:.6mm 1.6mm;height:fit-content;
  text-align:center}
.talk .say{flex:1 1 auto}

/* 表 */
table.fg{border-collapse:collapse;width:100%;margin:2.4mm 0 0;font-size:9.4pt}
table.fg th,table.fg td{border:.6pt solid var(--line);padding:1.8mm 2.4mm;
  text-align:left;vertical-align:top;line-height:1.65}
table.fg th{background:var(--accent-l);color:var(--accent);font-weight:700;font-size:8.6pt}
table.fg td:first-child{background:var(--paper);font-weight:600}
table.fg td.num{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
table.fg td.cn{white-space:nowrap}
.sw{display:inline-block;width:3.4mm;height:3.4mm;border-radius:50%;
  border:.5pt solid rgba(0,0,0,.25);margin-right:2mm;vertical-align:-.7mm}

/* 配置図 */
.shelf{display:flex;gap:4mm;margin:2.4mm 0 0}
.shelf .col{flex:1 1 0}
.shelf .cap{font-size:8pt;font-weight:700;color:var(--accent);text-align:center;
  background:var(--accent-l);border:.6pt solid var(--accent-b);border-bottom:0;
  border-radius:2pt 2pt 0 0;padding:1.4mm}
.shelf .cell{border:.6pt solid var(--accent-b);border-top:0;padding:2.4mm 1.4mm;
  text-align:center;font-size:9.6pt;line-height:1.5}
.shelf .cell:last-child{border-radius:0 0 2pt 2pt}
.shelf .cell small{display:block;color:var(--ink3);font-size:6.8pt}

/* 対比 */
.cmp{display:flex;gap:4mm;margin:2.4mm 0 0}
.cmp .col{flex:1 1 0;border:.6pt solid var(--line);border-radius:2pt;overflow:hidden}
.cmp .ch2{font-size:9pt;font-weight:700;color:var(--accent);background:var(--accent-l);
  padding:1.4mm 2mm;text-align:center}
.cmp ul{margin:0;padding:2mm 2mm 2mm 6mm}
.cmp li{font-size:9.2pt;line-height:1.7;padding-bottom:1.4mm}

/* タイムライン */
.tl{margin:2.4mm 0 0;border-left:1.4pt solid var(--accent-b);padding-left:4mm}
.tl .row{display:flex;gap:3mm;margin-bottom:2mm;position:relative}
.tl .row::before{content:"";position:absolute;left:-5.6mm;top:1.6mm;width:2.6mm;height:2.6mm;
  border-radius:50%;background:var(--accent)}
.tl .tm{flex:0 0 26mm;font-size:8.6pt;font-weight:700;color:var(--accent)}
.tl .ev{flex:1 1 auto;font-size:9pt;line-height:1.65}
.tl .ev small{display:block;font-size:8pt;color:var(--ink3)}
</style></head><body>
'''


def main():
    today = datetime.date.today().isoformat()
    items, sheets = load()
    html = render(items, sheets, today)
    out = os.path.join(HERE, f'Sasho_manual_full_{today}.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    n_sec = sum(len(s[1]) for s in SECTIONS.values())
    print(f"項目 {len(items)} / 章 {len(SECTIONS)} / 節 {n_sec}")
    if DROPPED:
        print(f"!! 【要確認】を{len(DROPPED)}件、成果物から除外しました（内部メモのため）:")
        for i, l in DROPPED:
            print(f"   ID{i} {l[:70]}")
    print(f"出力 {out} ({os.path.getsize(out)} bytes)")


if __name__ == '__main__':
    main()
