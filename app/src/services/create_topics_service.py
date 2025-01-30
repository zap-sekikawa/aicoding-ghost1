import json
import logging
from typing import List
from ..schema.schema import FortuneItems, FortuneItem, BrowsingHistory
from ..prompt.create_topics_prompts import create_topic_prompt
from ..utils.llm_client import call_claude_api

# ロガーの設定
logger = logging.getLogger(__name__)

def create_topics(browsing_history: List[BrowsingHistory]) -> FortuneItems:
    """
    閲覧履歴からトピックを生成する
    
    Args:
        browsing_history (List[dict]): 閲覧履歴データ
        
    Returns:
        FortuneItems: 生成されたトピックのリスト
        
    Raises:
        ValueError: LLMからの応答が不正な場合やトピック数が6件でない場合
    """
    logger.info("create_topics処理を開始します")
    # 1. プロンプト準備
    system_prompt = create_topic_prompt["system_prompt"]
    # BrowsingHistoryモデルをdictに変換
    browsing_history_dict = [history.dict() for history in browsing_history]
    user_prompt = create_topic_prompt["user_prompt"].format(
        browsing_history=json.dumps(browsing_history_dict, ensure_ascii=False)
    )
    
    logger.debug(f"システムプロンプト: {system_prompt}")
    logger.debug(f"ユーザープロンプト: {user_prompt}")
    
    # 2. LLM呼び出し
    logger.info("LLMを呼び出します")
    llm_response = call_claude_api(
        system_prompt=system_prompt,
        user_prompt=user_prompt
    )
    
    logger.debug(f"LLMレスポンス: {llm_response}")
    
    # 3. レスポンス(JSON形式)をパース
    #    {"items":[{"title":"xxx"},...]}
    try:
        json_obj = json.loads(llm_response)
        items_data = json_obj.get("items", [])
        
        if len(items_data) != 6:
            # 必須要件の6件なければエラー
            raise ValueError(f"create_topics: 6件のトピックが必要ですが、{len(items_data)}件が返却されました。")
        
        # 4. FortuneItemsモデルにバリデーション
        fortune_items = FortuneItems(items=[
            FortuneItem(title=item["title"]) for item in items_data
        ])
        logger.info(f"create_topics処理が成功しました。生成されたトピック数: {len(fortune_items.items)}")
        return fortune_items
    
    except json.JSONDecodeError as e:
        error_msg = f"LLMからの応答のJSONパースに失敗: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    except KeyError as e:
        error_msg = f"LLMからの応答に必要なキーが存在しません: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"create_topics処理でエラーが発生: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
