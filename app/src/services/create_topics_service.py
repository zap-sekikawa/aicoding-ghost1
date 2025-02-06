from typing import List
from schema.schema import ClientInput, FortuneItems, FortuneItem
from utils.llm_client import call_llm
from prompt.create_topics_prompts import get_create_topics_prompt

def create_topics(client_input: ClientInput) -> FortuneItems:
    """
    ユーザーの入力情報から占い項目を生成する。

    Args:
        client_input (ClientInput): ユーザーからの入力情報

    Returns:
        FortuneItems: 6つの占い項目
    """
    # プロンプトの生成
    prompt = get_create_topics_prompt(client_input)
    
    # LLMの呼び出し
    response = call_llm(prompt)
    
    # レスポンスをパースしてFortuneItemsを生成
    items: List[FortuneItem] = []
    for line in response.strip().split("\n"):
        if line:
            items.append(FortuneItem(title=line.strip()))
    
    return FortuneItems(items=items)
