from pydantic import BaseModel, Field, validator
from typing import List, Dict


class BrowsingHistory(BaseModel):
    """
    ユーザーのブラウジング履歴。
    """
    category: str
    title: str

class ClientInput(BaseModel):
    """
    ユーザーからの入力。
    """
    datetime: str
    birthday: str
    browsing_history: List[BrowsingHistory]


class FortuneItem(BaseModel):
    """
    create_topics(...) が返す占い項目の1つ。
    今回は titleのみ必要。
    """
    title: str


class FortuneItems(BaseModel):
    """
    create_topics(...) の最終出力。
    - items: FortuneItemを6つ格納した配列
    """
    items: List[FortuneItem]

    @validator("items")
    def check_six_items(cls, v):
        """fortune_itemsは常に6件であることを想定。"""
        if len(v) != 6:
            raise ValueError("fortune_items['items'] は常に6件でなければなりません。")
        return v


class LogicData(BaseModel):
    """
    logic_data.xml から解析した結果を格納。
    - personality: <explanation id='menu'> を含む<content>ブロックの text1
    - ghost_data: ghost_id -> 複数text1をユニーク化して連結した文字列
    - ghost_ids: 解析段階で得られた ghost_id のユニーク値一覧
    """
    personality: str
    ghost_data: Dict[int, str]
    ghost_ids: List[int]

    @validator("ghost_ids")
    def check_ghost_range(cls, v):
        """
        ghost_id のユニーク数は1〜5以内。
        また各ghost_id自体も 1〜5 しか許容しない想定なら、
        ここでチェックしてもよい。
        """
        if not (1 <= len(v) <= 5):
            raise ValueError(f"ghost_idのユニーク数が1〜5の範囲外です: {len(v)}")
        return v


class FortuneBlock(BaseModel):
    """
    ghost_idひとつに対して、対応するfortune_itemsを分割してまとめたもの。
    - ghost_id: 1〜5
    - fortune_titles: fortune_items の一部(titleだけ)を格納したリスト
    """
    ghost_id: int
    fortune_titles: List[FortuneItem]

    @validator("ghost_id")
    def ghost_id_must_be_in_range(cls, v):
        """
        ghost_idは1〜5でなければエラー。
        もし5(猫)等を許容するなら 1 <= v <= 5 に修正。
        """
        if not (1 <= v <= 5):
            raise ValueError(f"ghost_idが1〜5の範囲外です: {v}")
        return v


class GhostToneOutputItem(BaseModel):
    """
    ghost_tone_model から返ってくる「各アドバイス項目」。
    - title: ユーザーが見ている占い項目
    - content: 実際のアドバイス本文
    - ghost_id: どの守護霊からのアドバイスか
    """
    ghost_id: int
    title: str
    content: str

class SummarizedGhostToneOutputItem(BaseModel):
    """
    GhostToneOutputItem から要約を作成したあとの単一アイテムのスキーマ。
    - ghost_id: 守護霊ID (1〜5の範囲を想定)
    - item_index: 何番目の項目か
    - summary: 要約後のテキスト
    """
    ghost_id: int
    item_index: int
    summary: str

    @validator("ghost_id")
    def ghost_id_must_be_in_range(cls, v):
        if not (1 <= v <= 5):
            raise ValueError(f"ghost_idが1〜5の範囲外です: {v}")
        return v


class SummaryResult(BaseModel):
    """
    summary_model で20文字以内に要約した後の最終スキーマ。
    - ghost_id: 対応する守護霊ID
    - summary: 要約(20文字以内)
    - content: 元の全文
    """
    ghost_id: int
    summary: str 
    content: str


class ClientOutput(BaseModel):
    """
    ユーザーに返す出力。
    """
    results: List[SummaryResult]
