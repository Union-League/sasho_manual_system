# -*- coding: utf-8 -*-
"""①DB → web/data.json.js を再生成する。

/マニュアル更新 の最後に実行し、web/ をコミット＆pushすると
Cloudflare Pages が自動でHTML版マニュアルを更新する。
index.html は手を入れない（データだけ差し替わる）。

使い方:  python web/build_web.py
"""
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os, json, datetime

SA = os.path.expanduser('~/.sasho/service-account.json')
DB = '1VxEepC6PHtTO_Ic1JckaKMP9lItFCqhLLc5cpE2Gkkk'
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'data.json.js')

# CLAUDE.md 記載の13ジャンル固定順（②③PDFの章立てと同じ順序）
GENRES = ["開店・閉店作業", "メニュー・料金", "ドリンク", "客席・レイアウト",
          "オペレーション・接客", "清掃・衛生", "備品・在庫", "発注・仕入れ",
          "設備・機器", "安全管理", "予約・レジ", "調理・仕込み", "身だしなみ"]


def main(generated=None):
    creds = service_account.Credentials.from_service_account_file(
        SA, scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
    svc = build('sheets', 'v4', credentials=creds)

    # CL_ で始まるシートを動的に列挙（枚数を決め打ちしない）
    meta = svc.spreadsheets().get(spreadsheetId=DB).execute()
    cl_names = [s['properties']['title'] for s in meta['sheets']
                if s['properties']['title'].startswith('CL_')]

    cl = {}
    for name in cl_names:
        vals = svc.spreadsheets().values().get(
            spreadsheetId=DB, range=f"'{name}'!A1:B300").execute().get('values', [])
        cl[name] = [str(r[1]).strip() for r in vals[2:]
                    if len(r) >= 2 and str(r[0]).strip() and str(r[1]).strip()]

    # 図表シート（ID単位で表・配置図などの中身を持つ）
    figs, fig_kind = {}, {}
    fv = svc.spreadsheets().values().get(
        spreadsheetId=DB, range="'図表'!A3:H500").execute().get('values', [])
    for r in fv:
        if not r or not str(r[0]).strip():
            continue
        fid = str(r[0]).strip()
        kind = (r[1] if len(r) > 1 else '').strip()
        cells = [(r[i] if i < len(r) else '').strip() for i in range(2, 8)]
        while cells and not cells[-1]:
            cells.pop()
        if not cells:
            continue
        figs.setdefault(fid, []).append(cells)
        if kind:
            fig_kind[fid] = kind

    hdr = svc.spreadsheets().values().get(
        spreadsheetId=DB, range="マニュアルDB!A1:Q1").execute().get('values', [[]])[0]
    rows = svc.spreadsheets().values().get(
        spreadsheetId=DB, range="マニュアルDB!A2:Q400").execute().get('values', [])

    items, no_kw, missing_sheet = [], [], []
    for r in rows:
        if not r or not r[0]:
            continue
        d = {h: (r[i] if i < len(r) else '') for i, h in enumerate(hdr)}
        # ②③PDFと同じ条件：清書完了=TRUE かつ 有効
        if d['ステータス'] != '有効' or str(d['清書完了']).upper() != 'TRUE':
            continue
        sheet = d['チェックリストシート'].strip()
        if sheet and sheet not in cl:
            missing_sheet.append(d['ID'])
        if not d['検索キーワード'].strip():
            no_kw.append(d['ID'])
        items.append({
            "id": int(d['ID']),
            "genre": d['大ジャンル'].strip(),
            "title": d['タイトル'].strip(),
            "body": d['内容'].strip(),
            "kw": d['検索キーワード'].strip(),   # 検索専用。画面には表示しない
            "cl": cl.get(sheet, []) if sheet else [],
            "fk": fig_kind.get(d['ID'], ""),      # 表示形式（図表シート由来）
            "fg": figs.get(d['ID'], []),          # 図表データ
        })

    unknown = sorted({i['genre'] for i in items} - set(GENRES))
    payload = {
        "genres": [g for g in GENRES if any(i['genre'] == g for i in items)],
        "items": items,
        "generated": (generated or datetime.date.today().isoformat()) + " 更新",
    }
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('window.__SASHO__=' + json.dumps(payload, ensure_ascii=False,
                                                 separators=(',', ':')) + ';\n')

    n_fig = sum(1 for i in items if i['fg'])
    print(f"項目 {len(items)} / 章 {len(payload['genres'])} / CL {sum(len(i['cl']) for i in items)}項目 / 図表 {n_fig}件")
    orphan = sorted(set(figs) - {str(i['id']) for i in items})
    if orphan:
        print("!! 図表があるのに対象行でないID（廃止・未清書など）:", orphan)
    nokind = sorted([i['id'] for i in items if i['fg'] and not i['fk']])
    if nokind:
        print("!! 表示形式が未指定の図表:", nokind)
    print(f"出力 {OUT} ({os.path.getsize(OUT)} bytes)")
    if unknown:
        print("!! 未知の大ジャンル（章から漏れます）:", unknown)
    if missing_sheet:
        print("!! 参照先CLシートが見つからない行:", missing_sheet)
    if no_kw:
        print("!! 検索キーワード未入力（検索で引けません）:", no_kw)


if __name__ == '__main__':
    main()
