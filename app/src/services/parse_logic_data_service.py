from typing import Dict
import xml.etree.ElementTree as ET
from ..schema.schema import LogicData
import logging

logger = logging.getLogger(__name__)

def parse_logic_data(xml_str: str) -> LogicData:
    logger.info("XMLデータのパース処理を開始")
    """
    XMLデータをパースしてLogicDataを生成する
    
    Args:
        xml_str (str): パース対象のXML文字列
        
    Returns:
        LogicData: パース結果のLogicDataオブジェクト
        
    Raises:
        ValueError: XMLのパースに失敗した場合
    """
    try:
        logger.debug("XMLの解析を開始")
        root = ET.fromstring(xml_str)
        logger.debug("XMLの解析が完了")
    except ET.ParseError as e:
        error_msg = f"XMLのパースに失敗: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    personality = ""
    ghost_data_map: Dict[str, str] = {}
    ghost_ids = set()
    
    try:
        logger.debug("personalityの取得を開始")
        # <title>1</title>を含む<content>ブロックから<explanation id="text1">の内容を取得
        for content in root.findall("content"):
            title_elem = content.find("title")
            if title_elem is not None and title_elem.text == "1":
                text1_elem = content.find("./explanation[@id='text1']")
                if text1_elem is not None:
                    personality = text1_elem.text.strip()
                    logger.debug(f"personality取得完了: {personality[:30]}...")
                break  # personalityは1つのみ

        logger.debug("ghost_dataの取得を開始")
        # <explanation id="ghost">を含む<content>ブロックを探索
        for content in root.findall("content"):
            ghost_elem = content.find("./explanation[@id='ghost']")
            if ghost_elem is not None:
                ghost_id = ghost_elem.text.strip()
                ghost_ids.add(ghost_id)
                
                text1_elem = content.find("./explanation[@id='text1']")
                if text1_elem is not None:
                    text1 = text1_elem.text.strip()
                    if ghost_id not in ghost_data_map:
                        ghost_data_map[ghost_id] = text1
                    else:
                        # 同じghost_idが複数あれば結合（重複は除外）
                        existing = ghost_data_map[ghost_id]
                        if text1 not in existing:
                            ghost_data_map[ghost_id] = f"{existing}\n{text1}"
        
        logger.debug("ghost_idsの整形を開始")
        sorted_ghost_ids = sorted(list(ghost_ids), key=lambda x: int(x))
        
        logger.debug("LogicDataの生成を開始")
        logic_data = LogicData(
            personality=personality,
            ghost_data=ghost_data_map,
            ghost_ids=[int(g) for g in sorted_ghost_ids]
        )
        logger.info("XMLデータのパース処理が完了")
        logger.debug(f"生成されたLogicData: ghost_ids={logic_data.ghost_ids}")
        return logic_data
        
    except Exception as e:
        error_msg = f"LogicDataの生成に失敗: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg)
