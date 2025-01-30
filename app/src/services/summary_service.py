import json
import logging
from typing import List
from ..schema.schema import GhostToneOutputItem, SummaryResult
from ..prompt.summary_prompts import summary_prompt
from ..utils.llm_client import call_claude_api

logger = logging.getLogger(__name__)

def summary_model(ghost_tone_results: List[GhostToneOutputItem]) -> List[SummaryResult]:
    logger.info("summary_model処理を開始")
    """
    ghost_tone_modelの出力を20文字以内に要約する
    
    Args:
        ghost_tone_results (List[GhostToneOutputItem]): 要約対象のアドバイスリスト
        
    Returns:
        List[SummaryResult]: 要約結果のリスト
        
    Raises:
        ValueError: LLMからの応答が不正な場合やその他のエラー
    """
    try:
        # 1. LLMに投げるためのデータ準備
        logger.debug(f"要約対象のアイテム数: {len(ghost_tone_results)}")
        #    item_indexを付与して、後で元のcontentと紐付けられるようにする
        items_for_llm = []
        for i, item in enumerate(ghost_tone_results):
            items_for_llm.append({
                "ghost_id": item.ghost_id,
                "item_index": i,
                "title": item.title,
                "content": item.content
            })
        
        # 2. プロンプト準備
        logger.debug("プロンプトの準備を開始")
        system_prompt = summary_prompt["system_prompt"]
        user_prompt = summary_prompt["user_prompt"].format(
            list_of_GhostToneOutputItem=json.dumps(items_for_llm, ensure_ascii=False)
        )
        
        # 3. LLM呼び出し
        logger.debug("LLMを呼び出し")
        llm_response = call_claude_api(system_prompt, user_prompt)
        logger.debug("LLMからの応答を受信")
        
        # 4. JSONパース
        logger.debug("LLMレスポンスのJSONパースを開始")
        #    [{ "ghost_id":X, "item_index":Y, "summary":"..."},...]
        summaries = json.loads(llm_response)
        
        # 5. バリデーション
        logger.debug(f"バリデーション開始: {len(summaries)}件の要約をチェック")
        for summary in summaries:
            if not all(k in summary for k in ["ghost_id", "item_index", "summary"]):
                raise ValueError("必須キーが存在しません")
            if len(summary["summary"]) > 20:
                raise ValueError(f"要約が20文字を超えています: {len(summary['summary'])}文字")
        
        # 6. SummaryResultに変換
        logger.debug("SummaryResultへの変換を開始")
        #    ghost_id, summary, content(original)を含む
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
        
        logger.info(f"summary_model処理が完了: {len(summary_results)}件の要約を生成")
        return summary_results
        
    except json.JSONDecodeError as e:
        error_msg = f"LLMからの応答のJSONパースに失敗: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"summary_model処理でエラーが発生: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg)
