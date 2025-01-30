import requests
from typing import Optional

class ExternalRepository:
    def __init__(self, base_url: str):
        """
        外部APIリポジトリの初期化
        
        Args:
            base_url (str): 外部APIのベースURL
        """
        self.base_url = base_url.rstrip('/')  # 末尾のスラッシュを除去
    
    def get_logic_data(self) -> str:
        """外部サーバーからデータを取得し、XML文字列で返却"""
        try:
            response = requests.get(f"{self.base_url}/api/logic-data")
            response.raise_for_status()  # エラーレスポンスの場合は例外を発生
            return response.text
        except requests.RequestException as e:
            # ネットワークエラーやタイムアウトなどの例外をハンドリング
            raise ValueError(f"外部APIからのデータ取得に失敗: {str(e)}")
