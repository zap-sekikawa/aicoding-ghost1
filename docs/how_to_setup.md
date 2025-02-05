環境構築手順
本ドキュメントでは、Mac ローカル環境での開発・動作確認を想定した環境構築手順を記載しています。Docker 環境、AWS 上での検証・本番運用を想定した基本的な流れも含まれています。必ず記載の内容を順に実施し、前提条件を満たしているか都度チェックしてください。

1. 前提条件の確認
1-1. macOS のバージョン確認
```bash
sw_vers
```
macOS 13.x( Ventura ) 以上を推奨（12.x でも可）
その他のバージョンの場合でも動作する可能性はありますが、サポート対象外になる場合があります

1-2. Python のバージョン確認
```bash
python3 --version
```
Python 3.11.x を利用してください
インストールされていない場合、pyenv や Homebrew を利用し、Python 3.11 系をインストールしてください
Python 3.11 系以外では動作保証しません

1-3. Docker のインストール & バージョン確認
```bash
docker --version
```
Docker 20.x 以上であることを推奨
インストールされていない場合、Docker公式サイト から Docker Desktop for Mac をインストールしてください
Docker Desktop を起動し、正常に動作しているかを確認しておいてください

1-4. AWS CLI と AWS CDK (Python) のインストール & バージョン確認 (必要に応じて)
AWS 上での検証やデプロイを行う場合、以下を準備します。

```bash
# AWS CLI バージョン確認
aws --version

# AWS CDK (Python) バージョン確認
cdk --version
```
AWS CLI はバージョン 2.x を推奨
CDK は 2.x 系での動作を想定
どちらも未インストールの場合は公式ドキュメントに従いインストールしてください

2. リポジトリのクローンとブランチ運用
GitHub などからプロジェクトのリポジトリをクローンします（URL はプロジェクトメンバーに共有されている想定）

```bash
git clone <YOUR_REPO_URL>
```

クローンしたディレクトリへ移動
```bash
cd <YOUR_PROJECT_DIRECTORY>
```

ブランチポリシー
- 開発用: develop ブランチ
- 本番: main ブランチ
いずれかの作業ブランチを切って開発し、最終的に develop → main の順でマージする形を取ってください

3. .env ファイルの準備
本プロジェクトでは、環境変数の管理を .env ファイル で行います。
.env ファイルは機密情報を含むことが想定されるため、プロジェクトの .gitignore に含まれており、通常リポジトリにはコミットされません。

プロジェクトルートにある env.example を参考に、.env ファイルを作成してください

必要な環境変数を .env に書き込みます
- 機密情報、外部 API Key、AWS 関連のシークレット などは 絶対にコミットしない ようにしてください
- .env は開発・テストでのみ参照し、本番環境では別の手段（AWS Systems Manager Parameter Store など）を使う場合もあります
- .env ファイルや機密情報を読み取ったり改変したりしないように 運用にご注意ください。

4. Python 仮想環境のセットアップ（ローカル開発環境）
ローカル開発を行う場合は、プロジェクト用の仮想環境を作成し、依存パッケージをインストールします。
pyenv + venv, または virtualenv など好みの方法で構いません。

重要: プロジェクトの要件として、PYTHONPATHをapp/srcに設定する必要があります。

以下は例として venv を利用する場合:

プロジェクトルートで仮想環境を作成
```bash
python3 -m venv .venv
```

仮想環境を有効化し、PYTHONPATHを設定
```bash
# 仮想環境の有効化
source .venv/bin/activate

# PYTHONPATHの設定
# .venv/bin/activateに以下の行を追記することを推奨
export PYTHONPATH="$PWD/app/src:$PYTHONPATH"
```

依存パッケージのインストール
```bash
# requirements.txt にまとめられた依存関係をインストール
pip install --upgrade pip
pip install -r requirements.txt
```

インストールしたパッケージが正しく反映されているか確認
```bash
pip list
```
fastapi, uvicorn, boto3 (>=1.36.0), pydantic, などが表示されれば OK です
仮想環境の有効化は、ローカル実行中は必ず行ってください。

5. ローカル環境での起動
5-1. uvicorn の起動ポート確認
- ローカル開発時: http://127.0.0.1:8000 などポート 8000 を使用（デフォルト）
- Docker 実行時: コンテナ内で 8000 ポートを開け、ローカルの別ポートへポートフォワードする想定（例: 8080）

5-2. FastAPI の起動
```bash
# まだ仮想環境を有効化していない場合:
source .venv/bin/activate

# 実行中のuvicornプロセスを確認
ps aux | grep uvicorn

# もし実行中のプロセスがあれば停止
kill <PID>

# プロジェクトルート or app/src ディレクトリ上で起動
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```
もしポート 8000 がすでに使用中の場合、別のポートに変更してください。
（例: --port 8001 など）

5-3. 動作確認
FastAPI が起動したら、以下をブラウザで開いてみてください:

- http://127.0.0.1:8000/docs
  - Swagger UI が表示され、エンドポイント一覧が確認できます
- http://127.0.0.1:8000/fortune など設定したエンドポイントがあれば叩いてみてください
- LLM（Claude / Bedrock）呼び出し機能を確認する際は、.env ファイル で指定した認証情報やベース URL などが正しいかをチェックしてください。

6. Docker 環境での起動
Docker を使う場合、アプリケーションをコンテナ化し、ローカルや検証用のサーバー上で同じイメージを起動できます。

6-1. Docker イメージのビルド
```bash
# プロジェクトルートにある Dockerfile を利用
docker build -t <YOUR_IMAGE_NAME> .
```
YOUR_IMAGE_NAME は任意のイメージ名に置き換えてください

6-2. コンテナの起動
```bash
docker run -d -p 8080:8000 --env-file .env --name <YOUR_CONTAINER_NAME> <YOUR_IMAGE_NAME>
```
- -d : バックグラウンドで起動
- -p 8080:8000 : ホスト側ポート 8080 をコンテナ内部の 8000 ポートにマッピング
- --env-file .env : ホスト側の .env ファイルをコンテナ内に反映
  (機密情報の管理には細心の注意を払ってください)
- --name <YOUR_CONTAINER_NAME> : 起動するコンテナに任意の名前を付与

コンテナ起動後、http://127.0.0.1:8080/docs などにアクセスして動作確認 してください。

6-3. コンテナのログ確認
```bash
docker logs <YOUR_CONTAINER_NAME>
```
エラーが発生していないか確認してください。

6-4. コンテナの停止と削除
```bash
docker stop <YOUR_CONTAINER_NAME>
docker rm <YOUR_CONTAINER_NAME>
```

7. テストの実行
7-1. テストの種類
- Unit テスト: app/tests/test_services/ に格納されるサービスロジックのテスト
- Integration テスト: app/tests/test_endpoints/ に格納されるエンドポイントレベルのテスト
- E2E テスト: 本番環境に近い状態でのフロー全体テスト（必要に応じて）

7-2. テスト実行コマンド
```bash
# 仮想環境をアクティブ化している前提
# PYTHONPATHが正しく設定されていることを確認
echo $PYTHONPATH

# テストの実行
pytest app/tests
```
- Mock データ: app/tests/mockdata/ 配下の logic_data.xml や client_input.json を利用
  ※これらのmockデータファイルは変更禁止です。テストケース追加時は新しいmockファイルを作成してください。
- 結果: ターミナル上にテスト結果が出力され、エラーがあれば詳細が表示されます

8. AWS 環境へのデプロイ（検証 / 本番）
AWS でのデプロイを想定する場合、以下のステップを踏みます。
（詳細はプロジェクトルートの cdk/ ディレクトリなどにあるスクリプトや AWS CodePipeline / App Runner の設定を参照）

8-1. AWS CLI / CDK の設定
AWS CLIの設定では、プロジェクトで必要な2つのリージョンの設定が必要です：
- デフォルトリージョン（ap-northeast-1）
- Bedrock用リージョン（us-west-2）

以下の手順で両方のリージョンを設定します：

```bash
# デフォルトプロファイルの設定（ap-northeast-1用）
aws configure
AWS Access Key ID [None]: YOUR_ACCESS_KEY
AWS Secret Access Key [None]: YOUR_SECRET_KEY
Default region name [None]: ap-northeast-1
Default output format [None]: json

# Bedrock用プロファイルの設定（us-west-2用）
aws configure --profile bedrock
AWS Access Key ID [None]: YOUR_ACCESS_KEY
AWS Secret Access Key [None]: YOUR_SECRET_KEY
Default region name [None]: us-west-2
Default output format [None]: json
```

Bedrockを利用する際は、`--profile bedrock`オプションを使用するか、
環境変数で一時的にプロファイルを切り替えることができます：
```bash
export AWS_PROFILE=bedrock
```

プロジェクトルートの cdk/requirements.txt をインストール（CDK スタックで必要なライブラリがある場合）
```bash
pip install -r cdk/requirements.txt
```

cdk bootstrap（初回のみ）
CDK を利用するリージョン / アカウントで一度ブートストラップを行う

8-2. CDK スタックによるリソース作成
```bash
# cdk ディレクトリに移動
cd cdk

# デプロイしたいスタックを指定
cdk deploy AppRunnerStack
cdk deploy CodePipelineStack
```
ここで作成される AWS リソース (App Runner, CodeBuild/CodePipeline, ECR など) はプロジェクトのインフラ要件に応じて異なります

8-3. デプロイ完了後の動作確認
- AWS App Runner などで起動されたエンドポイントの URL を確認
- https://xxxxxxx.awsapprunner.com/fortune などにアクセスし、Swagger UI やエンドポイントが正常動作するか検証

9. セキュリティ・注意事項
機密情報の取り扱い
- .env に記載する内容はコミット禁止
- 他の機密ファイルやキー情報もコミット禁止

ログ出力
- 機密性の高い値をログに出力しない
- 外部 API Key、AWS シークレットキー、トークンなど絶対にログに出さない

テストデータの取り扱い
- app/tests/mockdata/ 配下のmockデータ（logic_data.xml, client_input.json）は変更禁止
- 新しいテストケースを追加する場合は、既存のmockデータを変更せず、新しいmockファイルを作成する

ベストプラクティス
- 本番環境では AWS Systems Manager Parameter Store や Secrets Manager で機密情報を管理
- Docker イメージも不要なパッケージを含めず、最小限のイメージを作成

10. よくあるトラブルシューティング
ポート競合
- Error: [Errno 98] Address already in use と表示された場合
  → 別のポートを指定して起動
  → 既存のuvicornプロセスを確認・停止

Docker Desktop が起動していない
- docker: command not found や Docker CLI でエラー
  → Docker Desktop を起動・インストール確認

Python バージョンが 3.11 でない
- 予期せぬエラーが出る可能性大
  → Python 3.11.x に切り替える or インストールしなおす

AWS CLI / CDK のバージョンの不整合
- cdk synth などでエラー
  → pip install --upgrade aws-cdk.core / cdk --version でのバージョン整合性を確認

11. まとめ
- 前提環境のバージョンや依存関係を厳守 してください
- ローカル実行時と Docker 実行時でポートや環境変数の扱いが異なる場合があります
- .env や機密ファイルは 絶対にコミットしない
- テストは pytest app/tests で随時実行し、ユニットテスト・結合テストを通過させてから PR してください
- AWS へのデプロイ時は CDK や CodePipeline のスタック設定を確認し、本番と検証環境で設定を分ける など慎重に行ってください

本手順に沿って環境を構築することで、ローカル・Docker・AWS（検証 / 本番）それぞれの環境で一貫した開発・デプロイを実施できます。環境差分をうまく管理しつつ、セキュリティと運用を考慮しながら開発を進めてください。
