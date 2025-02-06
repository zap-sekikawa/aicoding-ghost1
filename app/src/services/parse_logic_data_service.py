import xml.etree.ElementTree as ET
from typing import Dict, List, Set
from schema.schema import LogicData
from pathlib import Path

def parse_logic_data() -> LogicData:
    """
    logic_data.xmlを解析してLogicDataを生成する。

    Returns:
        LogicData: 解析結果
    """
    # XMLファイルの読み込み
    xml_path = Path(__file__).parent.parent.parent / "tests" / "mockdata" / "logic_data.xml"
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # personalityの取得（menu=2002のtext1）
    personality = ""
    ghost_data: Dict[int, List[str]] = {}
    ghost_ids: Set[int] = set()

    for content in root.findall("content"):
        menu = content.find("explanation[@id='menu']")
        if menu is not None and menu.text == "2002":
            text1 = content.find("explanation[@id='text1']")
            if text1 is not None:
                personality = text1.text.strip()
        
        # ghost_idとtext1の収集
        ghost = content.find("explanation[@id='ghost']")
        text1 = content.find("explanation[@id='text1']")
        if ghost is not None and text1 is not None:
            ghost_id = int(ghost.text)
            ghost_ids.add(ghost_id)
            if ghost_id not in ghost_data:
                ghost_data[ghost_id] = []
            ghost_data[ghost_id].append(text1.text.strip())

    # ghost_dataの各リストを連結してユニークな文字列に変換
    ghost_data_unique = {
        ghost_id: "\n".join(set(texts))
        for ghost_id, texts in ghost_data.items()
    }

    return LogicData(
        personality=personality,
        ghost_data=ghost_data_unique,
        ghost_ids=sorted(list(ghost_ids))
    )
