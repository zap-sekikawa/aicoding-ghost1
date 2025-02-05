# 環境構築およびセットアップ手順

本手順では、すでにリポジトリが git clone された状態から始める想定で、以下の4つの環境を構築・運用する流れを示します。

- ローカル開発環境 (Mac / Windows)
- Docker 環境
- AWS ステージング環境
- AWS 本番環境

## 前提条件

### OSの前提
- Mac または Windows (Home/Pro)
  - ※Windowsの場合は、PowerShell もしくは WSL 環境などでUnix系コマンドを利用できるとスムーズです。

### 必要なソフトウェアのインストール確認

以下のソフトウェアがあらかじめインストールされていることを必ず確認してください。インストールされていない場合は、各公式サイトなどからインストールを行ってください。

#### Python 3.11

バージョン確認コマンド:
```bash
python --version
```
または
```bash
python3 --version
```
3.11.x 以上が表示されることを確認

#### Docker

バージョン確認コマンド:
```bash
docker --version
```
20.x 以上が表示されることを確認

#### AWS CLI (ステージング/本番デプロイに必要)

バージョン確認コマンド:
```bash
aws --version
```
- AWS CLI v2 であることを確認
- `aws configure` を実施して、適切な AWS アクセスキーやリージョンが設定されていることを確認（デプロイ時に必要）

#### Node.js & npm (AWS CDK用)

バージョン確認コマンド:
```bash
node -v
npm -v
```
Node.js 16.x 以上を推奨

#### AWS CDK

バージョン確認コマンド:
```bash
cdk --version
```
2.x系がインストールされていることを確認

もし導入していない場合は、以下のようにnpm経由でインストール可能です。
```bash
npm install -g aws-cdk
```

## ディレクトリ構成

すでにリポジトリをクローン済みの場合、以下のようなディレクトリ構成になっているはずです。
コメント行は構成の意図を示すために残しています。

```
.
├── .env                               # 環境変数ファイル（※通常.gitignore対象）※読み取り、編集禁止
├── app                                # アプリケーションのルートフォルダ
│   ├── src                            # ソースコード
│   │   ├── main.py                   # FastAPIエントリポイント
│   │   ├── endpoints                 # ルーティングやエンドポイントを定義
│   │   │   └── fortune.py            # /fortune 等のエンドポイント例
│   │   ├── services                  # ビジネスロジックやLLM呼出し処理などをまとめる
│   │   │   ├── create_topics_service.py       # create_topics用サービス
│   │   │   ├── parse_logic_data_service.py    # XMLをパースしてLogicDataを生成するサービス
│   │   │   ├── ghost_tone_service.py          # ghost_tone_model（LLM）呼び出し
│   │   │   ├── summary_service.py             # 内容を20文字以内で要約するサービス
│   │   │   └── fortune_block_service.py       # 分割処理など
│   │   ├── repository               # データ取得リポジトリ
│   │   │   ├── mock_repository.py   # mockdataからデータ取得するリポジトリ
│   │   │   └── external_repository.py  # 外部APIなど本番用のデータ取得リポジトリ(将来的に)
│   │   ├── models                   # DBモデルやORマッパーを使うならここに置く
│   │   ├── utils                    # 共通ユーティリティ
│   │   │   └── llm_client.py        # 実際にClaude API呼び出しなどを行う処理
│   │   ├── data                     # 閲覧履歴がない時のデフォルトのトピックのデータを格納
│   │   │   └── default_topics.py    # 閲覧履歴がない時に使用するデフォルトのトピック
│   │   ├── prompt                   # プロンプトファイルを格納
│   │   │   ├── create_topics_prompts.py       # create_topics用のPrompt
│   │   │   ├── ghost_tone_prompts.py          # ghost_tone用のPrompt
│   │   │   ├── ghost_tone_nohistory_prompts.py  # 閲覧履歴がない時に使うghost_tone用のPrompt
│   │   │   └── summary_prompts.py             # summary用のPrompt
│   │   ├── config                       # 設定関連
│   │   │   └── settings.py             # 設定値を管理する
│   │   ├── schema                       # Pydanticスキーマ
│   │   │   └── schema.py               # FortuneItem, LogicData, FortuneBlockなどの定義、※編集禁止
│   │   └── __init__.py              # Pythonパッケージとして認識させるためのファイル
│   ├── tests                        # テスト関連
│   │   ├── mockdata                 # テスト用のモックデータ
│   │   │   ├── client_input.json    # リクエストボディのモックデータ、※編集禁止
│   │   │   └── logic_data.xml       # テスト用のロジックデータ（XML）、※編集禁止
│   │   ├── test_endpoints           # エンドポイントのユニット/結合テスト
│   │   ├── test_services            # サービス層のユニットテスト
│   │   └── __init__.py             # テスト用パッケージ
│   └── __init__.py                 # Pythonパッケージとして認識させるためのファイル
├── cdk                              # AWS CDKによるIaC
│   ├── app_runner_stack.py         # App Runner関連のスタック定義
│   ├── codepipeline_stack.py       # CodePipeline/CodeBuild関連のスタック定義
│   ├── requirements.txt            # CDKで利用するPythonライブラリの依存関係
│   └── __init__.py                 # CDK用パッケージ
├── doc                              # ドキュメント類
│   └── how_to_use_bedrock_claude.md  # Claude(Bedrock)を使ったLLM実装ガイド、※編集禁止
├── env.example                       # 環境変数のサンプル
├── .gitignore                       # git管理除外ファイル
├── Dockerfile                       # Dockerビルド用
├── requirements.txt                 # アプリケーションのPython依存関係
└── README.md                        # プロジェクト全体の説明

```

## 1. ローカル開発環境のセットアップ

### 1.1 リポジトリルートに移動

```bash
cd /path/to/fortune-project
```

クローン済みのリポジトリ直下へ移動してください。

### 1.2 Python仮想環境の作成と有効化

Mac / Unix系 (bash/zsh) の場合:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> Note: コマンドラインの先頭などに (venv) や (.venv) と表示されていればOKです。

### 1.3 依存関係のインストール

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 1.4 アプリケーションの起動

FastAPI の開発サーバを起動して動作確認を行います。

```bash
uvicorn app.src.main:app --reload --host 0.0.0.0 --port 8000
```

> Note: ブラウザで http://localhost:8000/docs にアクセスすると、FastAPI の自動ドキュメントが確認できます。

### 1.5 テストの実行

```bash
pytest
```

`app/tests/` 配下のテストが一括実行され、結果が表示されます。

## 2. Docker 環境

ローカルでの開発とは別に、Dockerコンテナとして実行したい場合の手順です。

### 2.1 Dockerfile の確認

リポジトリ直下にある Dockerfile を参照し、ベースイメージの Python バージョンなどを変更したい場合は適宜書き換えてください。
（例：`FROM python:3.11-slim` → `FROM python:3.11-alpine` など）

### 2.2 Docker イメージのビルド

```bash
docker build -t fortune-app:latest .
```

### 2.3 コンテナを起動

```bash
docker run -d -p 8000:8000 --name fortune-container fortune-app:latest
```

起動確認:

```bash
docker ps
```

`fortune-container` が稼働中になっていればOK

ブラウザで http://localhost:8000/docs にアクセスし、FastAPI のエンドポイント一覧が表示されることを確認してください。

## 3. AWS ステージング環境へのデプロイ

AWS にステージング用アプリケーションをデプロイする手順です。
App Runner や CodePipeline を用いた設定が `cdk/` ディレクトリ内に定義されています。

### 3.1 AWS CLI と AWS CDK のセットアップ確認

AWS CLI:

```bash
aws sts get-caller-identity
```

アカウント情報が表示されればOK

AWS CDK:

```bash
cdk --version
```

2.x系が表示されればOK

### 3.2 CDK の依存関係をインストール

```bash
cd cdk
pip install -r requirements.txt
cd ..
```

`cdk/requirements.txt` は CDK 用の Python ライブラリが記載されています。

### 3.3 CDK でデプロイ (ステージング)

初回の場合は CDK のブートストラップを実行してください。

```bash
cd cdk
cdk bootstrap
```

続いて、スタックをデプロイします。

```bash
cdk deploy --profile <aws_profile_name> --all
```

`--profile <aws_profile_name>` は複数の AWS プロファイルを使い分けている場合に指定してください。
指定しない場合は default プロファイルが使用されます。

デプロイ後、App Runner のURL等が表示されますので、そちらにアクセスして `/docs` 画面が出ればOKです。

## 4. AWS 本番環境へのデプロイ

ステージングとほぼ同様の手順で、本番用スタックをデプロイします。
（CDKの`app_runner_stack.py` や `codepipeline_stack.py` 内で、本番用に別途リソースを分けて管理する場合が多いです。）

```bash
cd cdk
cdk deploy --profile <aws_profile_name> ProductionPipelineStack
```

デプロイ完了後、App Runner などから公開されるURLにアクセスして動作を確認してください。

## 5. 環境変数管理 (.env ファイル)

- `.env` ファイルには機密情報や外部APIキー、設定値などを格納し、`.gitignore` に含めることが推奨されます。
- `app/config/settings.py` や `USE_MOCK = True/False` の切り替えなどもここで管理可能です。
- ステージング・本番など、異なる環境で値を変えたい場合は AWS Systems Manager Parameter Store や AWS Secrets Manager などを使うと安全です。

## 6. まとめ

### ローカル開発
- 仮想環境を作成 → `requirements.txt` のインストール
- uvicorn で FastAPI 起動 → http://localhost:8000/docs で確認
- pytest でテスト

### Docker コンテナ
- docker build → docker run
- http://localhost:8000/docs にアクセス

### AWS ステージング
- cdk bootstrap → cdk deploy
- CodePipeline + App Runner などによるデプロイ確認

### AWS 本番
- ステージングと同様の流れ
- 別スタックや別設定で本番向けにリソースを分離

以上の手順を踏むことで、占いアプリケーションの開発からテスト、本番環境運用まで一連のワークフローを構築できます。