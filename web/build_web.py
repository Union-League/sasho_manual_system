# -*- coding: utf-8 -*-
"""①DB → web/data.json.js を再生成する。

/マニュアル更新 の最後に実行し、web/ をコミット＆pushすると
Cloudflare Pages が自動でHTML版マニュアルを更新する。
index.html は手を入れない（データだけ差し替わる）。

使い方:  python web/build_web.py
"""
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os, re, json, datetime

RE_SHEET = re.compile(r'^ID\d+$')

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

    # 別シート「ID○○」を動的に列挙（枚数を決め打ちしない。増減するため）
    #   A1=【タイトル】/ B1=表示形式 / 2行目=列見出し / 3行目以降=データ
    #   B1が「チェックリスト」ならチェックリスト、それ以外は図表として扱う
    meta = svc.spreadsheets().get(spreadsheetId=DB).execute()
    names = [s['properties']['title'] for s in meta['sheets']
             if RE_SHEET.match(s['properties']['title'])]

    cl, figs, fig_kind = {}, {}, {}
    for name in names:
        vals = svc.spreadsheets().values().get(
            spreadsheetId=DB, range=f"'{name}'!A1:H300").execute().get('values', [])
        if not vals:
            continue
        head = vals[0]
        kind = (head[1].strip() if len(head) > 1 else '')
        fig_kind[name] = kind

        if kind == 'チェックリスト':
            cl[name] = [str(r[1]).strip() for r in vals[2:]
                        if len(r) >= 2 and str(r[0]).strip() and str(r[1]).strip()]
            continue

        # 表・対応表は2行目がそのままヘッダー行になる。それ以外（配置図・対比・
        # 色見本・タイムライン・手順）は列の意味が位置で決まるので列見出しは渡さない。
        body = vals[1:] if kind in ('表', '対応表') else vals[2:]
        rows_f = []
        for r in body:
            cells = [str(r[i]).strip() if i < len(r) else '' for i in range(6)]
            while cells and not cells[-1]:
                cells.pop()
            if cells:
                rows_f.append(cells)
        if rows_f:
            figs[name] = rows_f

    hdr = svc.spreadsheets().values().get(
        spreadsheetId=DB, range="マニュアルDB!A1:Q1").execute().get('values', [[]])[0]
    rows = svc.spreadsheets().values().get(
        spreadsheetId=DB, range="マニュアルDB!A2:Q400").execute().get('values', [])

    def strip_todo(text):
        """【要確認】は内部メモ。②③PDFと同様、成果物には出さない。"""
        keep, drop = [], []
        for line in text.split("\n"):
            (drop if '【要確認】' in line else keep).append(line)
        return "\n".join(keep).strip(), drop

    items, no_kw, missing_sheet, sheet_refs, todos = [], [], [], set(), []
    for r in rows:
        if not r or not r[0]:
            continue
        d = {h: (r[i] if i < len(r) else '') for i, h in enumerate(hdr)}
        # ②③PDFと同じ条件：清書完了=TRUE かつ 有効
        if d['ステータス'] != '有効' or str(d['清書完了']).upper() != 'TRUE':
            continue
        sheet = d['別シート'].strip()
        is_cl = sheet in cl
        if sheet:
            sheet_refs.add(sheet)
        if sheet and sheet not in cl and sheet not in figs:
            missing_sheet.append(d['ID'])
        if not d['検索キーワード'].strip():
            no_kw.append(d['ID'])
        body, dropped = strip_todo(d['内容'].strip())
        for x in dropped:
            todos.append((d['ID'], x.strip()))
        items.append({
            "id": int(d['ID']),
            "genre": d['大ジャンル'].strip(),
            "title": d['タイトル'].strip(),
            "body": body,
            "kw": d['検索キーワード'].strip(),   # 検索専用。画面には表示しない
            "cl": cl.get(sheet, []),                      # チェックリストの全項目
            "fk": "" if is_cl else fig_kind.get(sheet, ""),  # 表示形式（シートB1）
            "fg": figs.get(sheet, []),                    # 図表データ
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
    orphan = sorted((set(figs) | set(cl)) - sheet_refs, key=lambda t: int(t[2:]))
    if orphan:
        print("!! シートはあるがDBの別シート列から参照されていない:", orphan)
    nokind = sorted([i['id'] for i in items if i['fg'] and not i['fk']])
    if nokind:
        print("!! B1の表示形式が未指定:", nokind)
    print(f"出力 {OUT} ({os.path.getsize(OUT)} bytes)")
    if unknown:
        print("!! 未知の大ジャンル（章から漏れます）:", unknown)
    if missing_sheet:
        print("!! 参照先シートが見つからない行:", missing_sheet)
    if no_kw:
        print("!! 検索キーワード未入力（検索で引けません）:", no_kw)
    if todos:
        print(f"!! 【要確認】を{len(todos)}件、成果物から除外しました（内部メモのため）:")
        for i, x in todos:
            print(f"   ID{i} {x[:70]}")


if __name__ == '__main__':
    main()
