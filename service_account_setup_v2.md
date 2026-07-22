# サービスアカウント設定手順書 v2（1回きり・代表者1名が実施）

所要時間の目安: 30分。Google Cloudの操作に不慣れでも画面の指示通りで進められます。
手順4のみ3人全員が各自のPCで実施します（Mac/Windows別の手順あり）。

## 1. Google Cloudプロジェクトの作成

1. https://console.cloud.google.com/ にSashoで使うGoogleアカウントでログイン
2. 画面上部のプロジェクト選択 →「新しいプロジェクト」
3. プロジェクト名: `sasho-manual`（任意）→ 作成

## 2. APIの有効化（2つ）

「APIとサービス」→「ライブラリ」から以下を検索し、それぞれ「有効にする」:

- Google Sheets API
- Google Drive API

（マニュアルはPDFで生成するため、Docs APIは不要です）

## 3. サービスアカウントの作成と鍵の発行

1. 「IAMと管理」→「サービスアカウント」→「サービスアカウントを作成」
2. 名前: `sasho-manual-bot`（任意）→ 作成して続行 → ロールは付与不要でそのまま完了
3. 作成されたアカウントのメールアドレスをメモする
   （例: `sasho-manual-bot@sasho-manual.iam.gserviceaccount.com`）
4. そのアカウントをクリック →「キー」タブ →「鍵を追加」→「新しい鍵を作成」→ JSON
5. ダウンロードされたJSONファイルが「鍵」。**絶対にLINEやメールで平文共有しない**。
   受け渡しは共有Driveの限定フォルダ等で行い、受け取り後は削除する。

## 4. 鍵の配置（3人全員が各自のPCで実施）

やること: 手順3の鍵ファイルを、ホームフォルダ直下の `.sasho` フォルダに
`service-account.json` という名前で置く。全員が同じ場所に置くことで、
全員のClaude Codeが同じ設定（CLAUDE.md記載のパス）で動きます。

前提: 鍵ファイルがダウンロードフォルダにあること。
（AirDrop・Drive経由で受け取った場合は、まずダウンロードフォルダに置いてから始める）

### Macの場合

1. `⌘＋スペース` でSpotlightを開き「ターミナル」と入力してEnter
2. 以下を1行ずつ入力してEnter（1〜3行目は成功すると何も表示されません）

```bash
mkdir -p ~/.sasho
mv ~/Downloads/sasho-manual-*.json ~/.sasho/service-account.json
chmod 600 ~/.sasho/service-account.json
ls -l ~/.sasho/
```

3. 最後の行で `service-account.json` が表示されれば完了

### Windowsの場合

1. スタートボタンを右クリック →「ターミナル」（または「Windows PowerShell」）
2. 以下を1行ずつ入力してEnter

```powershell
mkdir $HOME\.sasho
mv $HOME\Downloads\sasho-manual-*.json $HOME\.sasho\service-account.json
icacls $HOME\.sasho\service-account.json /inheritance:r /grant:r "${env:USERNAME}:R"
ls $HOME\.sasho
```

3. 最後の行で `service-account.json` が表示されれば完了
   （3行目の権限設定はエラーが出ても動作に影響しないので飛ばして可）

### 共通の注意

- `sasho-manual-*.json` は実際のファイル名に合わせる。分からなければ
  ダウンロードフォルダでファイル名を確認（頭の数文字＋`*.json` でも動く）
- `No such file or directory` / `Cannot find path` エラー → 鍵ファイルの名前か場所が違う
- ターミナルを使いたくない場合は、Claude Codeに
  「ダウンロードフォルダの鍵ファイルを ~/.sasho/service-account.json に移動して」と頼んでもよい

## 5. 対象ファイル・フォルダの作成と共有

以下を用意し、**すべてサービスアカウントのメールアドレスに「編集者」として共有**する:

| 対象 | 操作 |
|---|---|
| ①マニュアルDB | 既存xlsxをGoogleスプレッドシートとしてDriveにインポート（または新規作成して移行） |
| ToDo管理表 | 既存（共有のみ実施） |
| 共有用フォルダ | Driveフォルダを新規作成（名前例:「Sashoマニュアル」）。②③のPDFが入る。スタッフには**このフォルダを閲覧者として共有** |
| マニュアル履歴 | Driveフォルダを新規作成。旧版PDFの退避先。**経営陣のみ**（スタッフには共有しない） |

②③のPDFファイル自体は初回の `/マニュアル更新` が自動生成するため、手動作成は不要。
Googleドキュメントは使わないため作成不要。

共有方法: 各ファイル/フォルダの「共有」→ サービスアカウントのメールアドレスを入力 → 編集者。
「通知を送信」のチェックは外してよい。

## 6. CLAUDE.mdへのID記入

各URLからIDを抜き出し、`CLAUDE.md` の「ファイルID」表のプレースホルダを置き換える:

- スプレッドシート: `https://docs.google.com/spreadsheets/d/【ここがID】/edit`
- フォルダ: `https://drive.google.com/drive/folders/【ここがID】`
- ②③PDFのIDは初回 `/マニュアル更新` 実行時に自動記録されるため、この時点では空欄でよい

## 7. 動作確認（誰か1人のClaude Codeで）

Claude Codeでこのプロジェクトを開き、次を依頼する:

> 「~/.sasho/service-account.json を使って、CLAUDE.mdに記載の①マニュアルDBの
> 1行目（ヘッダー）を読み取って表示して。google-api-python-clientが無ければpip installして」

ヘッダー列が表示されれば疎通OK。
あわせてPDF化の確認として次も依頼する:

> 「『こんにちは、Sashoです』とだけ書いたHTMLを作り、Chromeヘッドレスで
> PDF化してデスクトップに保存して」

日本語が正しく表示されたPDFができれば環境確認完了（3人全員のPCで実施推奨）。

## 8. 初回セットアップタスク（疎通確認後、Claude Codeに依頼）

1. ①DBに「清書完了」「転記元」列を追加し、既存86行へ
   清書完了=TRUE / 転記元=「連絡ノート移行」を一括セット
2. ToDo管理表2シートの右端に「取り込み済」列を追加（/取り込み初回実行時の自動追加でも可）
3. 既存マニュアル3点（インカム活用マニュアル・接客マニュアル・服装規定）の
   ①DBへの取り込み・分割（該当DocのURLをClaude Codeに渡す）
4. `/取り込み` 初回実行（48件見込み）→ 清書 → `/バッティング確認` → `/マニュアル更新` で②③初版生成
5. 初版生成時に表示される②③PDFのファイルIDをCLAUDE.mdに記入

## トラブルシューティング

- **403 PERMISSION_DENIED**: 対象ファイルがサービスアカウントに共有されていない。手順5を確認。
- **API has not been used**: 手順2のAPI有効化漏れ。エラーメッセージ内のURLから有効化。
- **PDFの日本語が□（豆腐）になる**: HTMLのfont-family指定を
  `"Hiragino Sans","Yu Gothic",sans-serif` にする（Mac/Windows両対応）。
- **Chromeが見つからない**: Chromeのインストール先が標準と違う。Claude Codeに
  「Chromeの実行ファイルを探して」と頼めば特定してくれる。
- **鍵を漏らした/漏らしたかも**: サービスアカウントの「キー」タブから該当鍵を削除し、
  新しい鍵を発行して3人に再配布する（ファイル共有はやり直し不要）。
