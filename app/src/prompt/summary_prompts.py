from schema.schema import GhostToneOutputItem

def get_summary_prompt(ghost_tone_output: GhostToneOutputItem) -> str:
    """
    アドバイス内容を20文字以内に要約するためのプロンプトを生成する。

    Args:
        ghost_tone_output (GhostToneOutputItem): 要約対象のアドバイス項目

    Returns:
        str: 生成されたプロンプト
    """
    prompt = f"""
以下のアドバイス内容を20文字以内で要約してください。

タイトル: {ghost_tone_output.title}
内容:
{ghost_tone_output.content}

要件:
1. 最も重要なメッセージや助言を抽出してください
2. 20文字以内で簡潔に表現してください
3. 具体的な行動や方向性が分かるようにしてください
4. 余計な説明は省いてください

出力形式:
要約文のみを出力してください。余計な説明は不要です。
"""
    return prompt
