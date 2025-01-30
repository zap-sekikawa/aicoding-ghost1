# 4. 実装のタスク分解

## A. FastAPI エンドポイント実装

### エンドポイント定義
- `app/src/endpoints/fortune.py` に `/fortune` などのエンドポイントを作成
- リクエストボディ(`ClientInput`)を受け取る POST メソッドを用意
- `browsing_history` の空チェック
  - 空の場合：`create_topics` をスキップし、`default_topics` を使用
  - 空でない場合：従来通り `create_topics` を呼び出し

### ビジネスロジック呼び出し
- リクエストボディをもとに `services` 下の関数を順次コール

## B. 閲覧履歴データ取得 & ロジックサーバーデータ取得

### 閲覧履歴データ
- `ClientInput` の `browsing_history` を閲覧履歴データとして読み込む

### Mock用リポジトリ
- `app/src/repository/mock_repository.py` を作成
- ファイル(`app/tests/mockdata/`)から ロジックサーバーデータ(`logic_data.xml`) を読み込む

### 実際の外部API取得用リポジトリ（将来的）
- `app/src/repository/external_repository.py` を作成
- 外部サーバー（ロジックサーバー）からデータを取得する処理を実装
- ロジックサーバーのアクセス方法は `docs/how_to_access_logic_server.md` を参照

### 設定ファイル or 環境変数で切り替え
- `app/config/settings.py` 内で `USE_MOCK = True/False` 等を管理し、リポジトリを切り替え

## C. create_topics (LLM呼出)

### サービス層 (create_topics_service.py)
- 閲覧履歴が空の場合：
  - このステップをスキップ
  - デフォルトのトピックデータを使用
  - LLM 呼び出しを行わない
- 閲覧履歴データは `ClientInput` の `browsing_history` を参照
- `create_topics_prompt` を呼び出し、`{browsing_history}` を埋め込んで LLM へリクエスト
- 返却された JSON をパースし、`FortuneItems`(Pydantic) としてバリデーション（6件のタイトル確認）
- 出力: `FortuneItems`

### LLM実装方法
- `docs/how_to_use_bedrock_claude.md` を参照
- API呼び出し部分は `utils/llm_client.py` などにまとめることも可

## D. XMLパース (parse_logic_data_service.py)

### サービス層
#### personalityの抽出
- `<title>1</title>` を含む `<content>` ブロックを探索
- その中の `<explanation id="text1">` の内容を personality として抽出

#### 守護霊データ(ghost_data)の抽出
- `<explanation id="ghost>` を含む `<content>` ブロックを探索
- 各ブロックから以下を取得：
  - キー：`<explanation id="ghost">` の値
  - 値：同じ `<content>` 内の `<explanation id="text1">` の内容
- 同じ守護霊IDの場合はテキストを結合

#### 守護霊ID(ghost_ids)の抽出
- 全ての `<explanation id="ghost">` の値を配列として収集
- 重複を排除
- 昇順にソート

### バリデーション
- Pydantic の `LogicData` を使って不正をチェック

## E. fortune_items 分割 → FortuneBlock

### 入力データ
- `FortuneItems`
  - items配列に6件の `FortuneItem` を保持
- `LogicData`
  - `ghost_ids` の配列に守護霊IDを保持

### 分割ルール
ghost_id のユニーク数 n (1~4) に応じて 6件の fortune_items を分割:
- n=1：[1,2,3,4,5,6] → 1つのブロック
- n=2：[1,2,3], [4,5,6] → 2つのブロック
- n=3：[1,2], [3,4], [5,6] → 3つのブロック
- n=4：[1], [2], [3,4], [5,6] → 4つのブロック

### 生成方法
1. `LogicData` の `ghost_ids` の要素数を取得
2. 要素数に応じた分割パターンを決定
3. `FortuneItems` の items 配列を分割パターンに従って分割
4. 各分割グループに対して：
   - `ghost_id`：`ghost_ids` の対応する値を設定
   - `fortune_titles`：分割されたタイトル群を設定

## F. ghost_tone_model (LLM呼出)

### 口調別アドバイス生成
分割したブロック(`FortuneBlock`)の配列の各要素に対して処理：

#### ghost_id対応表
- ghost_id=1：商人
- ghost_id=2：頑固親父
- ghost_id=3：おばあ
- ghost_id=4：花魁
- ghost_id=5：猫

#### 処理手順
1. `system_prompt`、`user_prompt` に以下のデータを埋め込む：
   - `{titles}`：`FortuneBlock` の `fortune_titles` の配列
   - `{personality}`：`LogicData` の personality
   - `{ghost_data}`：`LogicData` の ghost_data
2. LLMによるトークン生成
3. 生成されたトークンを `GhostToneOutputItem` のスキーマに従って配列に格納

### 出力形式
- LLMからの出力は JSON 配列：`[{"ghost_id": 1, "title": "xxx", "content": "yyy"}, ...]`
- これをパースし、`GhostToneOutputItem` の配列で受け取る

## G. summary_model (LLM呼出)

### 入力データ
`GhostToneOutputItem` の配列：
- ghost_id：守護霊のID
- title：タイトル
- content：本文内容

### 処理手順
1. 入力データの各アイテムに対して：
   - `app/src/prompts/summary_prompts.py` からプロンプトを取得
   - `system_prompt`、`user_prompt` に入力データを埋め込み
2. LLM は各アイテムの要約結果を `SummarizedGhostToneOutputItem` スキーマとして JSON 形式で返却
3. 生成されたトークンを `SummaryResult` のスキーマに従って配列に格納

### 20文字要約
- `ghost_tone_model` で得られた各要素の content を20文字以内に要約
- `summary_prompts.py` に定義したプロンプトを使用

### 出力格納
- `SummaryResult` の配列に変換
- ghost_id, summary, content を保持

## H. 最終結果まとめ

### 出力形式
- 出力スキーマは `ClientOutput`
- `results` は必ず1つ以上の `SummaryResult` を格納

### レスポンス例
```json
{
  "results": [
    {
      "ghost_id": 1,
      "summary": "●●(20文字以内)",
      "content": "要約元の長いアドバイス"
    },
    {
      "ghost_id": 2,
      "summary": "・・・",
      "content": "・・・"
    }
  ]
}
```

### バリデーション
- まとめたオブジェクトを Pydanticモデル経由で返却
