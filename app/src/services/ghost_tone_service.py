from typing import List
from schema.schema import (
    ClientInput,
    FortuneItem,
    LogicData,
    GhostToneOutputItem
)
from utils.llm_client import call_llm
from prompt.ghost_tone_prompts import get_ghost_tone_prompt
from prompt.ghost_tone_nohistory_prompts import get_ghost_tone_nohistory_prompt

def get_ghost_tone(
    client_input: ClientInput,
    ghost_id: int,
    fortune_titles: List[FortuneItem],
    logic_data: LogicData
) -> List[GhostToneOutputItem]:
    """
    指定された守護霊IDに基づいて、占い項目に対するアドバイスを生成する。

    Args:
        client_input (ClientInput): ユーザーからの入力情報
        ghost_id (int): 守護霊ID
        fortune_titles (List[FortuneItem]): この守護霊に割り当てられた占い項目
        logic_data (LogicData): ロジックデータ

    Returns:
        List[GhostToneOutputItem]: 生成されたアドバイス項目のリスト
    """
    # 閲覧履歴の有無に応じてプロンプトを選択
    if client_input.browsing_history:
        prompt = get_ghost_tone_prompt(
            client_input=client_input,
            ghost_id=ghost_id,
            fortune_titles=fortune_titles,
            logic_data=logic_data
        )
    else:
        prompt = get_ghost_tone_nohistory_prompt(
            client_input=client_input,
            ghost_id=ghost_id,
            fortune_titles=fortune_titles,
            logic_data=logic_data
        )

    # LLMの呼び出し
    response = call_llm(prompt)

    # レスポンスをパースしてGhostToneOutputItemのリストを生成
    outputs: List[GhostToneOutputItem] = []
    current_title = ""
    current_content = []

    for line in response.strip().split("\n"):
        line = line.strip()
        if line.startswith("タイトル:"):
            # 前のアイテムがあれば保存
            if current_title and current_content:
                outputs.append(GhostToneOutputItem(
                    ghost_id=ghost_id,
                    title=current_title,
                    content="\n".join(current_content)
                ))
            # 新しいアイテムの開始
            current_title = line[len("タイトル:"):].strip()
            current_content = []
        elif line:
            current_content.append(line)

    # 最後のアイテムを保存
    if current_title and current_content:
        outputs.append(GhostToneOutputItem(
            ghost_id=ghost_id,
            title=current_title,
            content="\n".join(current_content)
        ))

    return outputs
