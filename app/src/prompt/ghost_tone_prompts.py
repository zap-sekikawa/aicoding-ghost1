from typing import List
from schema.schema import ClientInput, FortuneItem, LogicData

def get_ghost_tone_prompt(
    client_input: ClientInput,
    ghost_id: int,
    fortune_titles: List[FortuneItem],
    logic_data: LogicData
) -> str:
    """
    ゴーストトーンを生成するためのプロンプトを生成する。

    Args:
        client_input (ClientInput): ユーザーからの入力情報
        ghost_id (int): 守護霊ID
        fortune_titles (List[FortuneItem]): この守護霊に割り当てられた占い項目
        logic_data (LogicData): ロジックデータ

    Returns:
        str: 生成されたプロンプト
    """
    # 閲覧履歴の文字列化
    history_text = "\n".join([
        f"- カテゴリ: {h.category}, タイトル: {h.title}"
        for h in client_input.browsing_history
    ])

    # 占い項目の文字列化
    titles_text = "\n".join([
        f"- {item.title}"
        for item in fortune_titles
    ])

    # 守護霊の性格データ取得
    ghost_personality = logic_data.ghost_data.get(ghost_id, "")

    prompt = f"""
あなたは守護霊として、ユーザーにアドバイスを提供します。

ユーザー情報:
- 誕生日: {client_input.birthday}
- 日時: {client_input.datetime}

閲覧履歴:
{history_text}

守護霊の性格:
{ghost_personality}

占い項目:
{titles_text}

要件:
1. 各占い項目に対して、守護霊の性格に基づいたアドバイスを提供してください
2. ユーザーの閲覧履歴を考慮して、関連する内容を含めてください
3. 守護霊の性格や口調を一貫して保ってください
4. 具体的で実践的なアドバイスを心がけてください

出力形式:
各項目について以下の形式で出力してください:

タイトル: [占い項目のタイトル]
[アドバイスの本文]

タイトル: [次の占い項目のタイトル]
[アドバイスの本文]

...以下同様
"""
    return prompt
