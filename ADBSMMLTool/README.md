# ADB SMML モデル生成ツール

**ソース一括ダウンロード： [ADBSMMLTool-source.zip](ADBSMMLTool-source.zip)**

ZIPを展開すると、下記のソース・設定例・テスト一式を含む `ADBSMMLTool/` フォルダーが作成されます。

ADBの表・ビューの定義とコメントから、OAC Semantic Modeler向けのSMMLと確認用Excelを生成するローカルPythonツールです。

## 基本フロー

1. ADBの接続・対象表を設定し、初版SMMLと確認用Excelを生成します。
2. 初版を**モデル用の非公開GitHubリポジトリのmain**へPushします。
3. OACで新規Semantic Modelを作成し、mainの初版をCloneします。
4. ExcelのE列で表示名、H列のTRUE/FALSEで公開対象からの除外・保持を指定します。Excelの行は削除しません。
5. 編集済みExcelを再取込みし、更新版SMMLと具体的な変更明細を確認します。
6. 更新版をモデル用リポジトリの更新用ブランチへPushし、初版と同じOACモデルでPullします。
7. Presentation Layerの改名・除外・保持結果を確認し、整合性チェック後に対象環境に応じてDeployと動作テストを実施します。

**この公開リポジトリはツールのソース配布用です。生成したSMMLを同期するモデル用リポジトリは、別途非公開で用意してください。** ツールはモデルのPush前に非公開リポジトリであることを検証します。

## セットアップ

Python 3.10以上とGitを用意します。macOS/Linuxの例：

```bash
cd ADBSMMLTool
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[ui,test]"
cp examples/config.example.json settings.json
```

`settings.json`には自分の環境の接続先、スキーマ、対象表、OAC接続参照を設定します。配布用設定は架空の接続先であり、そのままではADBに接続しません。

```bash
./run.sh
```

ブラウザーで `http://127.0.0.1:8501` を開きます。Windowsでは `.venv\Scripts\python -m streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false` を実行します。

## 認証情報

- パスワードとGitHub TokenはUIのマスク入力、または `ADB_PASSWORD` / `ADB_WALLET_PASSWORD` / `GITHUB_TOKEN` の環境変数を使用します。コード・JSON・Gitには保存しません。
- `ADB_USER`はADBユーザー名に使用します。
- Walletが必要な接続方式では、本機で保管したWalletのパスをローカル設定に指定します。**Wallet本体はこのリポジトリに含まれません。**
- `settings.json`、`*.local.json`、Wallet、秘密鍵、実環境の出力はGit管理対象外です。
- ADBの表・列・データ行は変更しません。メタデータ読取りと、ローカルのSMML・Excel生成を行います。
- Git同期とPushには明示的な確認が必要です。OACへの自動Deployは行いません。

## 接続なしの動作確認

`examples/metadata.synthetic.json`は配布用に作成した架空の2表の定義です。実環境から抽出したデータ・コメント・接続情報は含まれません。

```bash
.venv/bin/python -m smml_tool generate \
  --config examples/config.example.json \
  --metadata examples/metadata.synthetic.json \
  --out outputs/offline-example
.venv/bin/python -m smml_tool validate outputs/offline-example
.venv/bin/python -m pytest -q
```

既に存在する出力フォルダーは再利用せず、新しい名前を指定してください。実環境への接続テストやOACのDeployは、上記のオフラインテストには含まれません。

## 配布内容

- `app.py`：日本語Streamlit UI
- `smml_tool/`：メタデータ取得、SMML生成、Excel往復、検証、Git同期
- `schemas/`：SMML検証スキーマと参照元の記録（`SOURCES.json`）
- `examples/`：認証情報を含まない設定例と架空メタデータ
- `tests/`：接続せずに実行する単体テスト
- `scripts/workbook.mjs`：利用可能な場合に使用するExcel描画補助。通常はopenpyxlへフォールバックします。
- `ADBSMMLTool-source.zip`：同じ公開ソースの一括ダウンロード用アーカイブ

実環境の設定、パスワード、Token、Wallet、既存のExcel、生成モデル、ログ、仮想環境、社内の作業記録は含みません。依存ライブラリとOracleのSMMLスキーマは、それぞれの提供元の利用条件に従って使用してください。
