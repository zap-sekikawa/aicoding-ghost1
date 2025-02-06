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

    try:
        # Converseリクエストの作成
        response = bedrock.converse(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            system=[{"text": "あなたは有能なAIアシスタントです。"}],
            messages=[
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ],
            inferenceConfig={
                "maxTokens": 2000,
                "temperature": 0.7,
                "topP": 0.9
            }
        )

        # レスポンスの解析
        model_message = response["output"]["message"]
        if "content" in model_message:
            return model_message["content"][0]["text"].strip()
        return ""

    except Exception as e:
        raise Exception(f"LLM呼び出しに失敗しました: {str(e)}")
