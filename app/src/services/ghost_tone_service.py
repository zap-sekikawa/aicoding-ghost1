import json
import logging
from typing import List, Dict
from ..schema.schema import FortuneBlock, GhostToneOutputItem, LogicData
from ..prompt.ghost_tone_prompts import ghost_tone_prompt
from ..prompt.ghost_tone_nohistory_prompts import ghost_tone_nohistory_prompt
from ..utils.llm_client import call_claude_api

logger = logging.getLogger(__name__)

def ghost_tone_model(
    blocks: List[FortuneBlock], 
    logic_data: LogicData, 
    has_browsing_history: bool
) -> List[GhostToneOutputItem]:
    logger.info("ghost_tone_model処理を開始")
    """
    各FortuneBlockに対して、ghost_idに応じた口調でアドバイスを生成する
    
    Args:
        blocks (List[FortuneBlock]): FortuneBlockのリスト
        logic_data (LogicData): ロジックデータ
        has_browsing_history (bool): 閲覧履歴の有無
        
    Returns:
        List[GhostToneOutputItem]: 生成されたアドバイスのリスト
        
    Raises:
        ValueError: LLMからの応答が不正な場合やその他のエラー
    """
    results = []
    logger.info(f"処理対象のブロック数: {len(blocks)}")

    for i, block in enumerate(blocks, 1):
        logger.debug(f"ブロック {i}/{len(blocks)} の処理を開始")
        ghost_id = block.ghost_id
        titles = [{"title": ft.title} for ft in block.fortune_titles]
        personality = logic_data.personality
        reference = logic_data.ghost_data.get(str(ghost_id), "")
        
        try:
            # 1. プロンプト選択
            logger.debug(f"ghost_id {ghost_id} のプロンプト選択")
            if has_browsing_history:
                system_prompt = _get_system_prompt(ghost_id)
                user_prompt = _get_user_prompt(ghost_id).format(
                    titles=json.dumps(titles, ensure_ascii=False), 
                    personality=personality, 
                    reference=reference
                )
            else:
                # 閲覧履歴がない場合は別のプロンプトを使用
                system_prompt = _get_system_prompt_nohistory(ghost_id)
                user_prompt = _get_user_prompt_nohistory(ghost_id).format(
                    titles=json.dumps(titles, ensure_ascii=False), 
                    personality=personality, 
                    reference=reference
                )

            # 2. LLM呼び出し
            logger.debug("LLMを呼び出し")
            llm_response = call_claude_api(system_prompt, user_prompt)
            logger.debug("LLMからの応答を受信")
            
            # 3. JSONパース
            logger.debug("LLMレスポンスのJSONパースを開始")
            items = json.loads(llm_response)  # list of object
            logger.debug(f"パース完了: {len(items)}件のアイテムを取得")
            
            # 4. バリデーション
            logger.debug("レスポンスのバリデーションを開始")
            for item in items:
                if not all(k in item for k in ["ghost_id", "title", "content"]):
                    raise ValueError("必須キーが存在しません")
                    
                model = GhostToneOutputItem(
                    ghost_id=item["ghost_id"],
                    title=item["title"],
                    content=item["content"]
                )
                results.append(model)
                logger.debug(f"ghost_id {ghost_id} のアイテムを追加")

        except json.JSONDecodeError as e:
            error_msg = f"LLMからの応答のJSONパースに失敗: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"ghost_tone_model処理でエラーが発生: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg)
    
    logger.info(f"ghost_tone_model処理が完了: {len(results)}件のアイテムを生成")
    return results

def _get_system_prompt(ghost_id: int) -> str:
    """ghost_tone_prompts.py から system_prompt を取得"""
    prompts = _get_prompts_by_ghost_id(ghost_id, ghost_tone_prompt)
    return prompts["system_prompt"]

def _get_user_prompt(ghost_id: int) -> str:
    """ghost_tone_prompts.py から user_prompt を取得"""
    prompts = _get_prompts_by_ghost_id(ghost_id, ghost_tone_prompt)
    return prompts["user_prompt"]

def _get_system_prompt_nohistory(ghost_id: int) -> str:
    """ghost_tone_nohistory_prompts.py から system_prompt を取得"""
    prompts = _get_prompts_by_ghost_id(ghost_id, ghost_tone_nohistory_prompt)
    return prompts["system_prompt"]

def _get_user_prompt_nohistory(ghost_id: int) -> str:
    """ghost_tone_nohistory_prompts.py から user_prompt を取得"""
    prompts = _get_prompts_by_ghost_id(ghost_id, ghost_tone_nohistory_prompt)
    return prompts["user_prompt"]

def _get_prompts_by_ghost_id(ghost_id: int, prompts_dict: Dict) -> Dict:
    """ghost_idに対応するプロンプトを取得"""
    ghost_type_map = {
        1: "商人",
        2: "頑固親父",
        3: "おばあ",
        4: "花魁",
        5: "猫"
    }
    ghost_type = ghost_type_map.get(ghost_id)
    if not ghost_type:
        raise ValueError(f"未定義のghost_id: {ghost_id}")
        
    prompts = prompts_dict.get(ghost_type)
    if not prompts:
        raise ValueError(f"プロンプトが定義されていないghost_type: {ghost_type}")
        
    return prompts
