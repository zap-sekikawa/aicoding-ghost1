import os
import boto3
import json
from typing import Dict, Any

def call_llm(prompt: str) -> str:
    """
    AWS Bedrockを使用してLLM（Claude）を呼び出す。

    Args:
        prompt (str): LLMに送信するプロンプト

    Returns:
        str: LLMからの応答テキスト

    Raises:
        Exception: API呼び出しに失敗した場合
    """
    # Bedrockクライアントの初期化
    session = boto3.Session(
        region_name=os.getenv('AWS_BEDROCK_REGION', 'us-west-2')
    )
    bedrock = session.client(
        service_name='bedrock-runtime',
        region_name=os.getenv('AWS_BEDROCK_REGION', 'us-west-2')
    )

    # リクエストボディの作成
    body = {
        "prompt": prompt,
        "max_tokens_to_sample": 2000,
        "temperature": 0.7,
        "top_p": 0.9,
    }

    try:
        # Bedrockの呼び出し
        response = bedrock.invoke_model(
            modelId="anthropic.claude-v2",
            body=json.dumps(body)
        )
        
        # レスポンスの解析
        response_body = json.loads(response['body'].read())
        return response_body['completion'].strip()

    except Exception as e:
        raise Exception(f"LLM呼び出しに失敗しました: {str(e)}")
