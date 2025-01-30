# 実装手順ガイド

本ドキュメントでは、以下のような流れで実装を進めることを想定しています。各ステップの概要・実装ポイントを示します。

## 1. FastAPI エンドポイント実装

### 1-1. エンドポイント定義

**ファイル配置先**  
`app/src/endpoints/fortune.py`

**実装概要**
- POST `/fortune` を用意し、リクエストボディとして `ClientInput`(Pydanticモデル) を受け取る。
- `browsing_history` が空かどうかをチェックして、空であれば `create_topics` スキップ。
  - 空の場合：あらかじめ用意した `default_topics` (`app/src/data/default_topics.py`) を使用
  - 空でなければ： `create_topics_service.py` 内の関数を呼び出してトピックを生成
- その後、ビジネスロジック層へ順次処理を引き渡す。

### 1-2. サンプルコード構造

```python
# app/src/endpoints/fortune.py

from fastapi import APIRouter, HTTPException
from app.schema.schema import ClientInput, ClientOutput
from app.src.services.create_topics_service import create_topics
from app.src.services.parse_logic_data_service import parse_logic_data
from app.src.services.ghost_tone_service import ghost_tone_model
from app.src.services.summary_service import summary_model
from app.src.data.default_topics import default_fortune_items
from app.src.repository.mock_repository import MockRepository  # or external_repository

router = APIRouter()

@router.post("/fortune", response_model=ClientOutput)
def get_fortune(client_input: ClientInput):

    # 1. 閲覧履歴取得
    browsing_history = client_input.browsing_history

    # 2. create_topics or default_topics
    if len(browsing_history) == 0:
        # 閲覧履歴が空の場合 -> default_fortune_items
        fortune_items = default_fortune_items  # Pydanticモデルと整合性をとる
    else:
        # 閲覧履歴がある場合 -> LLM呼び出し
        fortune_items = create_topics(browsing_history)

    # 3. ロジックデータ取得 (mock or external)
    #    設定ファイルのUSE_MOCKなどに応じてRepositoryを切り替える想定
    repository = MockRepository() 
    logic_data_xml = repository.get_logic_data()  # logic_data.xml文字列を取得
    logic_data = parse_logic_data(logic_data_xml)

    # 4. FortuneBlock分割
    #    ghost_idsの個数に合わせてfortune_itemsをブロック分割
    #    ※ ghost_tone_service or専用サービスで行うかで設計は変動可
    from app.src.services.fortune_block_service import split_fortune_items
    fortune_blocks = split_fortune_items(fortune_items, logic_data.ghost_ids)

    # 5. ghost_tone_model呼び出し
    ghost_tone_results = ghost_tone_model(fortune_blocks, logic_data, has_browsing_history=(len(browsing_history)>0))

    # 6. summary_model呼び出し
    summary_results = summary_model(ghost_tone_results)

    # 7. 出力成形
    #    PydanticのClientOutputを使い、最終レスポンスを生成
    output = ClientOutput(results=summary_results)
    return output
```

## 2. 閲覧履歴データ取得 & ロジックサーバーデータ取得

### 2-1. 閲覧履歴データ
- `ClientInput` の `browsing_history` フィールドを使用する。
- エンドポイント内で `browsing_history = client_input.browsing_history` のように取得する。

### 2-2. ロジックサーバーデータ(外部API or ファイルMock)
- 実際は外部APIなどから取得を想定。
- 本番環境用(`external_repository.py`) と、モック用(`mock_repository.py`) を用意し、設定で切り替えられるようにする。

**(1) mock_repository.py**

```python
# app/src/repository/mock_repository.py

import os

class MockRepository:
    def __init__(self):
        # 必要に応じて初期化
        pass

    def get_logic_data(self) -> str:
        """mockdata/logic_data.xml を読み込み、XML文字列として返却"""
        mock_data_path = os.path.join(
            os.path.dirname(__file__), 
            "../../tests/mockdata/logic_data.xml"
        )
        with open(mock_data_path, "r", encoding="utf-8") as f:
            data = f.read()
        return data
```

**(2) external_repository.py**

```python
# app/src/repository/external_repository.py

import requests

class ExternalRepository:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def get_logic_data(self) -> str:
        """外部サーバーからデータを取得し、XML文字列で返却"""
        # 例: 
        # response = requests.get(f"{self.base_url}/api/logic-data")
        # return response.text
        # 実装時は適宜修正
        pass
```

### 2-3. 設定ファイル or 環境変数で切り替え
`app/config/settings.py` で `USE_MOCK = True/False` を管理し、エンドポイント内で `if USE_MOCK: MockRepository() else: ExternalRepository(...)` のように切り替え。

## 3. create_topics (LLM呼出)

### 3-1. 処理概要
- 閲覧履歴が空でない場合に実施。
- Pydanticのスキーマである `FortuneItems` (`items: list[FortuneItem]`) を返す想定。
- LLM呼び出し後に、レスポンスのJSONをパースし、6件のタイトルを検証。
- 6件以外・JSONパース失敗・フォーマット異常の際にはエラー対応など適宜。

### 3-2. サービス層

```python
# app/src/services/create_topics_service.py

import json
from typing import List
from app.schema.schema import FortuneItems, FortuneItem
from app.src.prompt.create_topics_prompts import create_topic_prompt
from app.src.utils.llm_client import call_claude_api  # 例: 具体的にはBedrockなど

def create_topics(browsing_history: List[dict]) -> FortuneItems:
    # 1. prompt準備
    system_prompt = create_topic_prompt["system_prompt"]
    user_prompt = create_topic_prompt["user_prompt"].format(
        browsing_history=browsing_history
    )
    
    # 2. LLM呼び出し
    llm_response = call_claude_api(
        system_prompt=system_prompt,
        user_prompt=user_prompt
    )
    
    # 3. レスポンス(JSON形式)をパース
    #    {"items":[{"title":"xxx"},...]}
    try:
        json_obj = json.loads(llm_response)
        items_data = json_obj.get("items", [])
        
        if len(items_data) != 6:
            # 必須要件の6件なければ何らかのハンドリング
            raise ValueError("create_topics: 6 items not returned from LLM.")
        
        # 4. FortuneItemsモデルにバリデーションさせる
        fortune_items = FortuneItems(items=[
            FortuneItem(title=item["title"]) for item in items_data
        ])
        return fortune_items
    
    except json.JSONDecodeError as e:
        # エラー処理
        raise ValueError(f"Invalid JSON from LLM: {e}")
```

## 4. XMLパース (parse_logic_data_service.py)

### 4-1. 処理概要

**personality**
- `<title>1</title>` を含む `<content>` ブロック探す
- その中の `<explanation id="text1">` の内容を文字列として抽出

**守護霊データ(ghost_data)**
- `<explanation id="ghost">` を含む `<content>` ブロックを探索
- その `<ghost>` の値をキー、その `<content>` 内の `<explanation id="text1">` 値をまとめて保存。
- 同じキー(ghost_id)が複数ある場合は文字列を結合して重複削除

**守護霊ID(ghost_ids)**
- すべての `<explanation id="ghost">` から値を収集し、重複を除外して昇順ソート

### 4-2. サービス実装例

```python
# app/src/services/parse_logic_data_service.py

from typing import Dict
import xml.etree.ElementTree as ET
from app.schema.schema import LogicData

def parse_logic_data(xml_str: str) -> LogicData:
    root = ET.fromstring(xml_str)
    
    personality = ""
    ghost_data_map: Dict[str, str] = {}
    ghost_ids = set()
    
    for content in root.findall("content"):
        title_elem = content.find("title")
        if title_elem is not None and title_elem.text == "1":
            # personality
            text1_elem = content.find("./explanation[@id='text1']")
            if text1_elem is not None:
                personality = text1_elem.text.strip()

        ghost_elem = content.find("./explanation[@id='ghost']")
        if ghost_elem is not None:
            ghost_id = ghost_elem.text.strip()
            ghost_ids.add(ghost_id)
            
            text1_elem = content.find("./explanation[@id='text1']")
            if text1_elem is not None:
                text1 = text1_elem.text.strip()
                if ghost_id not in ghost_data_map:
                    ghost_data_map[ghost_id] = text1
                else:
                    # 同じghost_idが複数あれば結合
                    existing = ghost_data_map[ghost_id]
                    # 重複しないように
                    if text1 not in existing:
                        ghost_data_map[ghost_id] = existing + text1
    
    # 重複排除・昇順ソート
    sorted_ghost_ids = sorted(list(ghost_ids), key=lambda x: int(x))
    
    # LogicDataバリデーション
    logic_data = LogicData(
        personality=personality,
        ghost_data=ghost_data_map,
        ghost_ids=[int(g) for g in sorted_ghost_ids]
    )
    return logic_data
```

## 5. fortune_items 分割 → FortuneBlock

### 5-1. 入力データ
- FortuneItems
  - 6件の FortuneItem を保持 (items: List[FortuneItem])
- LogicData
  - ghost_ids: List[int] (1〜4件程度想定)

### 5-2. 分割ルール

| ghost_idsの要素数 n | fortune_items(6件) の分割 |
|-------------------|------------------------|
| 1 | [1,2,3,4,5,6] → 1つのブロック |
| 2 | [1,2,3], [4,5,6] → 2つのブロック |
| 3 | [1,2], [3,4], [5,6] → 3つのブロック |
| 4 | [1], [2], [3,4], [5,6] → 4つのブロック |

### 5-3. 実装例

```python
# app/src/services/fortune_block_service.py

from typing import List
from app.schema.schema import FortuneItems, FortuneBlock

def split_fortune_items(fortune_items: FortuneItems, ghost_ids: List[int]) -> List[FortuneBlock]:
    n = len(ghost_ids)  # ユニーク守護霊ID数
    items = fortune_items.items  # 6件
    
    if n == 1:
        # [0..5]
        block_slices = [(0, 6)]
    elif n == 2:
        # [0..2], [3..5]
        block_slices = [(0, 3), (3, 6)]
    elif n == 3:
        # [0..2), [2..4), [4..6)
        block_slices = [(0, 2), (2, 4), (4, 6)]
    elif n == 4:
        # [0..1), [1..2), [2..4), [4..6)
        block_slices = [(0, 1), (1, 2), (2, 4), (4, 6)]
    else:
        # n > 4は想定外(デザイン上)だが一応エラーや例外処理
        block_slices = [(0, 6)]  # 全部まとめるなど適宜

    fortune_blocks = []
    for i, (start, end) in enumerate(block_slices):
        ghost_id = ghost_ids[i]  # i番目のghost_id
        block_items = items[start:end]
        fortune_blocks.append(FortuneBlock(
            ghost_id=ghost_id,
            fortune_titles=block_items
        ))
    return fortune_blocks
```

## 6. ghost_tone_model (LLM呼出)

### 6-1. 処理概要
- 分割後の FortuneBlock の各要素に対して、口調別アドバイス生成 を行う。
- ghost_id に基づき、 `ghost_tone_prompts.py`(または `ghost_tone_nohistory_prompts.py`) の該当プロンプトを選択する。
- LLM からの出力は JSON 形式（GhostToneOutputItem の配列）を想定。

例:
```json
[
  {
    "ghost_id": 1,
    "title": "タイトル1",
    "content": "アドバイス"
  },
  ...
]
```

### 6-2. 実装イメージ

```python
# app/src/services/ghost_tone_service.py

import json
from typing import List
from app.schema.schema import FortuneBlock, GhostToneOutputItem
from app.src.prompt.ghost_tone_prompts import ghost_tone_prompts
from app.src.prompt.ghost_tone_nohistory_prompts import ghost_tone_prompts_nohistory
from app.src.utils.llm_client import call_claude_api

def ghost_tone_model(blocks: List[FortuneBlock], logic_data, has_browsing_history: bool) -> List[GhostToneOutputItem]:
    results = []

    for block in blocks:
        ghost_id = block.ghost_id
        titles = [{"title": ft.title} for ft in block.fortune_titles]
        personality = logic_data.personality
        reference = logic_data.ghost_data.get(str(ghost_id), "")
        
        # 1. プロンプト選択
        if has_browsing_history:
            system_prompt = _get_system_prompt(ghost_id)
            user_prompt = _get_user_prompt(ghost_id).format(
                titles=titles, 
                personality=personality, 
                reference=reference
            )
        else:
            # 閲覧履歴がない場合
            # ghost_tone_nohistory_prompts.py の該当箇所を使用
            system_prompt = _get_system_prompt_nohistory(ghost_id)
            user_prompt = _get_user_prompt_nohistory(ghost_id).format(
                titles=titles, 
                personality=personality, 
                reference=reference
            )

        # 2. LLM呼び出し
        llm_response = call_claude_api(system_prompt, user_prompt)
        
        # 3. JSONパース
        try:
            items = json.loads(llm_response)  # list of object
            for item in items:
                # Pydanticでバリデーション
                model = GhostToneOutputItem(
                    ghost_id=item["ghost_id"],
                    title=item["title"],
                    content=item["content"]
                )
                results.append(model)

        except Exception as e:
            # JSONエラーなどのハンドリング
            raise ValueError(f"ghost_tone_model parse error: {str(e)}")
    return results

def _get_system_prompt(ghost_id: int) -> str:
    # ghost_tone_prompts.py から system_prompt をghost_idに応じて取得するロジック
    if ghost_id == 1:
        return ghost_tone_prompts["商人"]["system_prompt"]
    elif ghost_id == 2:
        return ghost_tone_prompts["頑固親父"]["system_prompt"]
    elif ghost_id == 3:
        return ghost_tone_prompts["おばあ"]["system_prompt"]
    elif ghost_id == 4:
        return ghost_tone_prompts["花魁"]["system_prompt"]
    elif ghost_id == 5:
        return ghost_tone_prompts["猫"]["system_prompt"]
    else:
        # デフォルト
        return ""

def _get_user_prompt(ghost_id: int) -> str:
    # ghost_tone_prompts.py から user_prompt をghost_idに応じて取得
    if ghost_id == 1:
        return ghost_tone_prompts["商人"]["user_prompt"]
    # ...以下同様
    # 省略
    return ""

def _get_system_prompt_nohistory(ghost_id: int) -> str:
    # ghost_tone_nohistory_prompts.py から同様に取得
    return ""

def _get_user_prompt_nohistory(ghost_id: int) -> str:
    # ghost_tone_nohistory_prompts.py から同様に取得
    return ""
```

## 7. summary_model (LLM呼出)

### 7-1. 処理手順
- `ghost_tone_model` の出力（ `GhostToneOutputItem` のリスト）を入力とする。
- 各アイテム（ghost_id, title, content）について、20文字以内の要約を生成。
- `summarizedGhostToneOutputItem` のような中間形式(ghost_id, item_index, summary)を受け取ってから、最終的には `SummaryResult` (ghost_id, summary, content) へマッピングする。

### 7-2. 実装例

```python
# app/src/services/summary_service.py

import json
from typing import List
from app.schema.schema import GhostToneOutputItem, SummaryResult
from app.src.prompt.summary_prompts import summarry_prompt
from app.src.utils.llm_client import call_claude_api

def summary_model(ghost_tone_results: List[GhostToneOutputItem]) -> List[SummaryResult]:
    
    # 1. LLMに投げるため、GhostToneOutputItem配列をJSON文字列に
    #    ここで item_index を付与しておく
    items_for_llm = []
    for i, item in enumerate(ghost_tone_results):
        items_for_llm.append({
            "ghost_id": item.ghost_id,
            "item_index": i,
            "title": item.title,
            "content": item.content
        })
    
    system_prompt = summarry_prompt["system_prompt"]
    user_prompt = summarry_prompt["user_prompt"].format(
        list_of_GhostToneOutputItem=json.dumps(items_for_llm, ensure_ascii=False)
    )
    
    # 2. LLM呼び出し
    llm_response = call_claude_api(system_prompt, user_prompt)
    
    # 3. JSONパース
    #    [{ "ghost_id":X, "item_index":Y, "summary":"..."},...]
    try:
        summaries = json.loads(llm_response)
    except Exception as e:
        raise ValueError(f"Summary LLM response parse error: {e}")
    
    # 4. SummaryResultに落とし込む
    #    ghost_id, summary, content(original)
    summary_results = []
    for summary_item in summaries:
        ghost_id = summary_item["ghost_id"]
        item_index = summary_item["item_index"]
        summary_text = summary_item["summary"]
        
        # 対応する ghost_tone_results から content を再取得
        original_content = ghost_tone_results[item_index].content
        
        sr = SummaryResult(
            ghost_id=ghost_id,
            summary=summary_text,
            content=original_content
        )
        summary_results.append(sr)
    
    return summary_results
```

## 8. 最終結果まとめ

### 8-1. 出力形式
レスポンススキーマ： `ClientOutput`

```python
class ClientOutput(BaseModel):
    results: List[SummaryResult]
```

`results` の中に `ghost_id`, `summary`, `content` を格納した配列が1つ以上存在する。

### 8-2. サンプルレスポンス

```json
{
  "results": [
    {
      "ghost_id": 1,
      "summary": "●●(20文字以内)",
      "content": "要約元の長いアドバイス"
    },
    ...
  ]
}
```

上記のような形式でエンドポイント(`/fortune`)が最終的なJSONを返却する。
