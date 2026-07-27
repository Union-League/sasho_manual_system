# -*- coding: utf-8 -*-
"""②完全版のCSS・共通部品・表紙・目次を組み立てる（本文は body_ch*.html を連結）"""
import os, json, glob

HERE = os.path.dirname(os.path.abspath(__file__))
GEN_JP = "2026年7月28日"
GEN = "2026-07-28"

CHAPTERS = [
    ("開店・閉店作業", 5), ("メニュー・料金", 8), ("ドリンク", 18), ("客席・レイアウト", 7),
    ("オペレーション・接客", 40), ("清掃・衛生", 12), ("備品・在庫", 8), ("発注・仕入れ", 3),
    ("設備・機器", 10), ("安全管理", 7), ("予約・レジ", 13), ("調理・仕込み", 1), ("身だしなみ", 5),
]

CSS = """
@page { size:A4 portrait; margin:16mm 15mm; }
:root{
  --ink:#1a1a1a; --ink-2:#4a4a4a; --ink-3:#767676;
  --accent:#2b4257; --accent-l:#eaeef2; --accent-b:#c3ced8;
  --ng:#9c3428; --ng-bg:#fbf1ef; --ok:#2f6b4f; --ok-bg:#eff5f1;
  --warn:#8a6521; --warn-bg:#fbf6ea; --line:#dfe3e7; --paper:#fafafa;
  --mincho:"Hiragino Mincho ProN","Yu Mincho","YuMincho",serif;
  --gothic:"Hiragino Sans","Yu Gothic","Meiryo",sans-serif;
}
*{box-sizing:border-box}
html{-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{font-family:var(--gothic);color:var(--ink);font-size:10pt;line-height:1.8;margin:0}

/* 表紙 */
.cover{height:252mm;display:flex;flex-direction:column;justify-content:center;
  text-align:center;page-break-after:always}
.cover .mk{font-family:var(--mincho);font-size:9pt;letter-spacing:.55em;color:var(--accent);margin-bottom:11mm}
.cover h1{font-family:var(--mincho);font-size:30pt;font-weight:600;letter-spacing:.18em;margin:0 0 5mm}
.cover .sb{font-family:var(--mincho);font-size:12.5pt;color:var(--ink-2);letter-spacing:.5em;margin-bottom:15mm}
.cover .rl{width:32mm;height:1.5pt;background:var(--accent);margin:0 auto 15mm}
.cover .dt{font-size:10pt;color:var(--ink-3);letter-spacing:.12em}
.cover .nt{margin:16mm auto 0;max-width:126mm;padding:5mm 6mm;border:.5pt solid var(--accent-b);
  background:var(--paper);font-size:8.8pt;line-height:1.9;color:var(--ink-2);text-align:left}

/* 目次 */
.toc{page-break-after:always}
.toc h2{font-family:var(--mincho);font-size:15pt;letter-spacing:.24em;margin:0 0 8mm;
  padding-bottom:3mm;border-bottom:1.5pt solid var(--accent)}
.toc ol{list-style:none;padding:0;margin:0;counter-reset:t}
.toc li{counter-increment:t;border-bottom:.5pt dotted var(--accent-b);display:flex;
  align-items:baseline;gap:3mm;padding:3.4mm 1mm}
.toc li::before{content:"第" counter(t) "章";flex:0 0 15mm;font-family:var(--mincho);
  font-size:8.5pt;color:var(--accent)}
.toc .nm{flex:1;font-size:11pt}
.toc .ct{font-size:8.5pt;color:var(--ink-3)}

/* 章 */
.ch{page-break-before:always}
.ch-open{border-top:3pt solid var(--accent);padding-top:6mm;margin-bottom:9mm}
.ch-eb{font-family:var(--mincho);font-size:8.5pt;letter-spacing:.34em;color:var(--accent)}
.ch-nm{font-family:var(--mincho);font-size:23pt;font-weight:600;letter-spacing:.1em;margin:2mm 0 4mm}
.ch-ld{font-size:9.4pt;line-height:1.95;color:var(--ink-2);max-width:152mm}
.ch-mp{display:flex;flex-wrap:wrap;gap:1.5mm;margin-top:5mm;padding-top:4mm;border-top:.5pt solid var(--line)}
.ch-mp span{font-size:8pt;color:var(--accent);background:var(--accent-l);
  border:.5pt solid var(--accent-b);border-radius:2px;padding:.8mm 2.2mm}

/* 節・項目 */
.sec{margin-bottom:8mm}
.sec-h{display:flex;align-items:baseline;gap:3mm;margin:0 0 4mm;padding-bottom:2mm;
  border-bottom:1pt solid var(--accent)}
.sec-n{font-family:var(--mincho);font-size:8.5pt;letter-spacing:.1em;color:#fff;
  background:var(--accent);padding:.9mm 2.4mm;border-radius:2px;flex:0 0 auto}
.sec-t{font-family:var(--mincho);font-size:13pt;font-weight:600;letter-spacing:.06em}
.it{page-break-inside:avoid;margin-bottom:5mm}
.it-h{display:flex;align-items:baseline;gap:2mm;font-size:10.6pt;font-weight:600;
  margin:0 0 1.6mm;line-height:1.5}
.it-h::before{content:"";flex:0 0 auto;width:2.6mm;height:2.6mm;background:var(--accent);
  transform:rotate(45deg);margin-top:1mm}
.id{font-size:7.4pt;font-weight:400;color:var(--ink-3);letter-spacing:.04em;white-space:nowrap}
.it p{margin:0 0 1.6mm} .it p:last-child{margin-bottom:0}
.it-b{padding-left:4.6mm}
.loose{page-break-inside:auto}

/* 部品 */
.note{border-left:2pt solid var(--accent-b);background:var(--paper);padding:2.4mm 3.4mm;
  margin:2.4mm 0 0;font-size:8.8pt;color:var(--ink-2);line-height:1.75}
.note b{color:var(--accent);font-weight:600}
.warn{border:.5pt solid #ddc9a4;border-left:2.6pt solid var(--warn);background:var(--warn-bg);
  padding:2.6mm 3.4mm;margin:2.4mm 0 0;font-size:9pt;line-height:1.75}
.warn b{color:var(--warn)}
.danger{border:.5pt solid #e3c7c2;border-left:3pt solid var(--ng);background:var(--ng-bg);
  padding:3mm 3.6mm;margin:2.4mm 0 0;font-size:9.2pt;line-height:1.75}
.danger b{color:var(--ng)}
.cmp{display:flex;gap:3mm;margin:2.6mm 0 0}
.cmp>div{flex:1;border-radius:2px;padding:2.4mm 3mm;font-size:8.9pt;line-height:1.7}
.bad{border:.5pt solid #e3c7c2;border-left:2.6pt solid var(--ng);background:var(--ng-bg)}
.good{border:.5pt solid #c6dbcd;border-left:2.6pt solid var(--ok);background:var(--ok-bg)}
.cmp .lb{display:block;font-size:7.6pt;font-weight:600;letter-spacing:.1em;margin-bottom:1mm}
.bad .lb{color:var(--ng)} .good .lb{color:var(--ok)}
table{width:100%;border-collapse:collapse;margin:2.6mm 0 0;font-size:9pt}
th,td{border:.5pt solid var(--line);padding:1.8mm 2.4mm;text-align:left;vertical-align:top}
th{background:var(--accent-l);color:var(--accent);font-weight:600;font-size:8.4pt;
  letter-spacing:.06em;white-space:nowrap}
td.k{background:var(--paper);font-weight:600;white-space:nowrap}
td.num{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
.fmt{border:.5pt dashed var(--accent-b);background:#fcfdfd;padding:3mm 4mm;margin:2.6mm 0 0;
  font-size:9.2pt;line-height:2.05}
.fmt .q{font-family:var(--mincho);color:var(--accent);font-weight:600}
.fmt .blank{display:inline-block;min-width:9mm;border-bottom:.8pt solid var(--ink-3);margin:0 .6mm}
.talk{margin:2.6mm 0 0}
.talk .ln{display:flex;gap:2.6mm;margin-bottom:1.6mm;font-size:9pt;line-height:1.7}
.talk .who{flex:0 0 25mm;font-size:8.2pt;font-weight:600;color:var(--accent);text-align:right;padding-top:.3mm}
.talk .say{flex:1;background:var(--paper);border-radius:2px;padding:1.6mm 2.6mm;
  border-left:1.6pt solid var(--accent-b)}
.steps{counter-reset:s;list-style:none;padding:0;margin:2.6mm 0 0}
.steps li{counter-increment:s;position:relative;padding-left:8mm;margin-bottom:1.8mm;font-size:9.2pt;line-height:1.7}
.steps li::before{content:counter(s);position:absolute;left:0;top:.2mm;width:5mm;height:5mm;
  border-radius:50%;background:var(--accent);color:#fff;font-size:7.4pt;display:flex;
  align-items:center;justify-content:center;font-weight:600}
.rules{list-style:none;padding:0;margin:2.6mm 0 0;counter-reset:r}
.rules>li{counter-increment:r;border:.5pt solid var(--line);border-top:2pt solid var(--accent);
  border-radius:2px;padding:2.6mm 3.2mm;margin-bottom:2.6mm;page-break-inside:avoid}
.rules>li>.rh{font-size:9.8pt;font-weight:600;margin-bottom:1.2mm}
.rules>li>.rh::before{content:counter(r);display:inline-flex;width:4.6mm;height:4.6mm;
  border-radius:50%;background:var(--accent);color:#fff;font-size:7.2pt;align-items:center;
  justify-content:center;margin-right:2mm;vertical-align:1px}
.rules>li>p{font-size:8.9pt;color:var(--ink-2);margin:0;line-height:1.75}
.sw{display:inline-block;width:3.6mm;height:3.6mm;border-radius:50%;
  border:.5pt solid rgba(0,0,0,.3);margin-right:1.8mm;vertical-align:-.5mm}

/* フロー図（縦タイムライン） */
.flow{margin:3mm 0 0}
.ph{margin-bottom:4mm;page-break-inside:avoid}
.ph-h{display:flex;align-items:center;gap:2.4mm;margin-bottom:2mm}
.ph-h .b{flex:0 0 auto;font-family:var(--mincho);font-size:8.6pt;letter-spacing:.14em;color:#fff;
  background:var(--accent);padding:1mm 3mm;border-radius:10mm}
.ph-h .r{flex:1;height:.5pt;background:var(--accent-b)}
.ph-h .n{flex:0 0 auto;font-size:7.6pt;color:var(--ink-3)}
.ph ol{list-style:none;padding:0 0 0 3mm;margin:0;border-left:1.2pt solid var(--accent-b)}
.ph ol li{position:relative;padding:0 0 2.2mm 7mm;font-size:9.2pt;line-height:1.72}
.ph ol li:last-child{padding-bottom:0}
.ph ol li .num{position:absolute;left:-3.6mm;top:.2mm;width:5.2mm;height:5.2mm;border-radius:50%;
  background:#fff;border:1.2pt solid var(--accent);color:var(--accent);font-size:7pt;
  font-weight:600;display:flex;align-items:center;justify-content:center}

/* 1日のタイムライン */
.day{margin:3mm 0 0;border-left:1.5pt solid var(--accent-b);padding-left:0}
.day .row{display:flex;gap:3mm;align-items:flex-start;position:relative;padding:0 0 3mm 5mm}
.day .row:last-child{padding-bottom:0}
.day .row::before{content:"";position:absolute;left:-1.9mm;top:1.4mm;width:3.2mm;height:3.2mm;
  border-radius:50%;background:var(--accent)}
.day .tm{flex:0 0 26mm;font-family:var(--mincho);font-size:9.4pt;font-weight:600;color:var(--accent)}
.day .ev{flex:1;font-size:9.4pt;line-height:1.65}
.day .ev small{display:block;color:var(--ink-3);font-size:8.2pt;margin-top:.4mm}

/* 順序（矢印） */
.seq{display:flex;flex-wrap:wrap;align-items:stretch;gap:0;margin:2.6mm 0 0}
.seq .n{border:.5pt solid var(--accent-b);background:var(--paper);border-radius:2px;
  padding:2mm 3mm;font-size:9pt;text-align:center;min-width:26mm}
.seq .n b{display:block;font-size:9.6pt;color:var(--accent)}
.seq .n small{display:block;color:var(--ink-3);font-size:7.6pt;margin-top:.5mm;line-height:1.5}
.seq .ar{display:flex;align-items:center;color:var(--accent-b);padding:0 1.6mm;font-size:11pt}

/* くつ箱配置図 */
.shoe{display:flex;gap:5mm;margin:2.6mm 0 0}
.shoe .col{flex:1}
.shoe .cap{font-size:8.4pt;font-weight:600;color:var(--accent);text-align:center;
  background:var(--accent-l);border:.5pt solid var(--accent-b);border-bottom:none;padding:1.2mm}
.shoe .cell{border:.5pt solid var(--accent-b);border-top:none;padding:2.2mm 2mm;font-size:9pt;
  text-align:center;background:#fff}
.shoe .cell small{color:var(--ink-3);font-size:7.6pt}
"""


def cover_toc():
    toc = ['<section class="toc"><h2>目次</h2><ol>']
    for name, n in CHAPTERS:
        toc.append(f'<li><span class="nm">{name}</span><span class="ct">{n}項目</span></li>')
    toc.append('</ol></section>')
    return f"""<div class="cover">
  <div class="mk">SASHO</div>
  <h1>Sasho マニュアル</h1>
  <div class="sb">完全版</div>
  <div class="rl"></div>
  <div class="dt">{GEN_JP} 版</div>
  <div class="nt">
    このPDFは{GEN_JP}にマニュアルDBから自動生成されました。修正・追加の要望は経営陣へ。<br>
    このPDFを直接編集しても、次回の更新で消えます。
  </div>
</div>
""" + "\n".join(toc)


bodies = []
for f in sorted(glob.glob(os.path.join(HERE, 'body_ch*.html')),
                key=lambda p: int(''.join(c for c in os.path.basename(p) if c.isdigit()))):
    with open(f, encoding='utf-8') as fh:
        bodies.append(fh.read())

doc = f"""<meta charset="UTF-8">
<title>Sasho マニュアル 完全版</title>
<style>{CSS}</style>
{cover_toc()}
{"".join(bodies)}
"""
out = os.path.join(HERE, f'Sasho_manual_full_{GEN}.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(doc)
print("wrote", out)
print("chapters merged:", len(bodies))
