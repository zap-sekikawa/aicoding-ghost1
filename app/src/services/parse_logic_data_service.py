import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Set
from schema.schema import LogicData
from pathlib import Path
import xmltodict
from pydantic import BaseModel
import binascii
from pyDes import triple_des, CBC, PAD_NORMAL
import requests
import ssl
import urllib3.poolmanager as poolmanager
from datetime import datetime, timezone

import ssl

UID = "ZappallasX"

class InputParam(BaseModel):
    key: str
    value: str


class TLSAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        ctx = ssl.create_default_context()
        # デフォルトの暗号設定を SECLEVEL=1 に変更
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        self.poolmanager = poolmanager.PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_version=ssl.PROTOCOL_TLS,
            ssl_context=ctx)

def get_logicsrv_xml(input_params: List[InputParam]) -> str:
    """
    ロジックサーバから結果XMLを取得する

    Args:
        input_params (List[InputParam]): リクエストパラメータのリスト

    Returns:
        str: ロジックサーバからのレスポンスXML

    Raises:
        Exception: リクエスト失敗時のエラー
    """
    # メニューID
    m = "6320"

    # 現在時刻を取得してキー生成用の文字列を作成
    utc_now = datetime.now(timezone.utc)
    utc_now_str = utc_now.strftime("%Y%m%d%H%M%S") 
    data = utc_now_str + UID

    # 環境変数から設定値を取得
    url = os.getenv("LOGICSRV_ENDPOINT")
    sid = os.getenv("LOGICSRV_SID")
    key = os.getenv("LOGICSRV_KEY")
    vec = os.getenv("LOGICSRV_VEC")

    # Triple DESで暗号化
    k = triple_des(
        binascii.unhexlify(key),
        CBC,
        binascii.unhexlify(vec),
        pad=None,
        padmode=PAD_NORMAL
    )
    encrypted = k.encrypt(data)
    encrypted_hex = binascii.hexlify(encrypted).decode()

    # リクエストパラメータの設定
    params = {
        "sid": sid,
        "m": m,
        "uid": UID,
        "key": encrypted_hex,
        "rwMenu": "1",
    }

    # 追加のパラメータを設定
    for input_param in input_params:
        params[input_param.key] = input_param.value

    # GETリクエストを送信
    try:
        session = requests.session()
        session.mount('https://', TLSAdapter())
        response = session.get(url, params=params)
        response.raise_for_status()  # エラーレスポンスをチェック
        return response.text
    except requests.exceptions.RequestException as e:
        raise Exception(f"ロジックサーバへのリクエストに失敗しました: {str(e)}")


def get_mock_logicsrv_xml(input_params: List[InputParam]) -> str:
    """
    モックデータのXMLファイルを読み込んで返す関数

    Args:
        input_params (List[InputParam]): 入力パラメータのリスト(この関数では使用しない)

    Returns:
        str: モックデータのXML文字列

    Raises:
        FileNotFoundError: モックデータファイルが存在しない場合
        ValueError: モックデータファイルが空の場合
        UnicodeDecodeError: 文字エンコーディングエラーの場合
        Exception: その他の予期せぬエラーの場合
    """
    try:
        # モックデータファイルのパスを生成
        xml_path = Path(__file__).parent.parent.parent / "tests" / "mockdata" / "logic_data.xml"
        
        # ファイルの存在チェック
        if not xml_path.exists():
            raise FileNotFoundError(f"モックデータファイルが見つかりません: {xml_path}")
            
        # ファイルを読み込み
        with open(xml_path, 'r', encoding='shift_jis') as xml_file:
            xml_data = xml_file.read()
            if not xml_data:
                raise ValueError("モックデータファイルが空です")
            return xml_data
            
    except FileNotFoundError as e:
        raise FileNotFoundError(f"モックデータファイルの読み込みに失敗しました: {str(e)}")
    except UnicodeDecodeError as e:
        raise UnicodeDecodeError(f"文字エンコーディングエラー: {str(e)}")
    except Exception as e:
        raise Exception(f"モックデータの取得中に予期せぬエラーが発生しました: {str(e)}")





def parse_logic_data(date: str, birth: str) -> LogicData:
    """
    logic_data.xmlを解析してLogicDataを生成する。

    Returns:
        LogicData: 解析結果
    """
    if not (date.isdigit() and birth.isdigit() and len(date) == 8 and len(birth) == 8):
        raise ValueError("date と birth は8桁の数字である必要があります")
    print("USE_MOCK: ", os.getenv("USE_MOCK"))

    input_params = [
        InputParam(key="date", value=date),
        InputParam(key="birth", value=birth),
    ]


    if os.getenv("USE_MOCK") != "TRUE":
        xml_data = get_mock_logicsrv_xml(input_params)
    else:
        xml_data = get_logicsrv_xml(input_params)
    # print("====================================")
    # # print("xml_data: ", xml_data)
    # print("====================================")

        
    root = ET.fromstring(xml_data)

    result = root.find("result")
    if result is None or result.text != "2000":
        raise ValueError("uranai/resultの値が2000ではありません")

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

    print("ghost_data: ", ghost_data)

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
