import os

class MockRepository:
    def __init__(self):
        # 必要に応じて初期化処理を追加
        pass

    def get_logic_data(self) -> str:
        """mockdata/logic_data.xml を読み込み、XML文字列として返却"""
        mock_data_path = os.path.join(
            os.path.dirname(__file__), 
            "../../tests/mockdata/logic_data.xml"
        )
        with open(mock_data_path, "r", encoding="utf-8") as f:
            data = f.read()
        return data
