from schema.schema import ClientInput

def get_create_topics_prompt(client_input: ClientInput) -> str:
    """
    占い項目を生成するためのプロンプトを生成する。

    Args:
        client_input (ClientInput): ユーザーからの入力情報

    Returns:
        str: 生成されたプロンプト
    """
    # 閲覧履歴の文字列化
    history_text = ""
    if client_input.browsing_history:
        history_text = "最近の閲覧履歴:\n" + "\n".join([
            f"- カテゴリ: {h.category}, タイトル: {h.title}"
            for h in client_input.browsing_history
        ])

    prompt = f"""
あなたは占い師です。以下の情報に基づいて、ユーザーに関連する6つの占い項目を生成してください。

ユーザー情報:
- 誕生日: {client_input.birthday}
- 日時: {client_input.datetime}
{history_text}

要件:
1. 各項目は1行で表現してください
2. 具体的で個人的な内容にしてください
3. ユーザーの閲覧履歴を考慮して、関連する内容を含めてください
4. 仕事、恋愛、健康など、様々な分野をカバーしてください
5. 必ず6つの項目を生成してください

出力形式:
項目を1行ずつ出力してください。余計な説明は不要です。

出力例:
仕事での新しいチャレンジについて
恋愛関係の進展について
健康管理と運動習慣について
家族との関係について
金運と資産管理について
自己啓発と成長について
"""
    return prompt
