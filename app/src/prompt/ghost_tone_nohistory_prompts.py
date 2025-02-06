from typing import List
from schema.schema import ClientInput, FortuneItem, LogicData

def get_ghost_tone_nohistory_prompt(
    client_input: ClientInput,
    ghost_id: int,
    fortune_titles: List[FortuneItem],
    logic_data: LogicData
) -> str:
    """
    閲覧履歴がない場合のゴーストトーンを生成するためのプロンプトを生成する。

    Args:
        client_input (ClientInput): ユーザーからの入力情報
        ghost_id (int): 守護霊ID
        fortune_titles (List[FortuneItem]): この守護霊に割り当てられた占い項目
        logic_data (LogicData): ロジックデータ

    Returns:
        str: 生成されたプロンプト
    """
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

守護霊の性格:
{ghost_personality}

占い項目:
{titles_text}

要件:
1. 各占い項目に対して、守護霊の性格に基づいたアドバイスを提供してください
2. 誕生日と日時から読み取れる一般的な運勢を考慮してください
3. 守護霊の性格や口調を一貫して保ってください
4. 具体的で実践的なアドバイスを心がけてください
5. 初めての利用者向けに、より基本的で汎用的なアドバイスを提供してください

出力形式:
各項目について以下の形式で出力してください:

タイトル: [占い項目のタイトル]
[アドバイスの本文]

タイトル: [次の占い項目のタイトル]
[アドバイスの本文]

...以下同様
"""
    return prompt
