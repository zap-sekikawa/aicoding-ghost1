import os
import time
import json
import logging
import boto3
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError
from botocore.config import Config

logger = logging.getLogger(__name__)

class BedrockError(Exception):
    """Bedrock APIに関連するエラーの基底クラス"""
    pass

class BedrockClientError(BedrockError):
    """クライアント側のエラー（認証、パラメータ不正など）"""
    pass

class BedrockServiceError(BedrockError):
    """サービス側のエラー（サーバーエラー、タイムアウトなど）"""
    pass

def call_claude_api(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 2000,
    temperature: float = 0.0,
    top_p: float = 0.9,
    max_retries: int = 6
) -> str:
    logger.info("Claude API呼び出しを開始")
    """
    AWS Bedrock経由でClaude APIを呼び出す（Converse API使用）
    
    Args:
        system_prompt (str): システムプロンプト（必須推奨）
        user_prompt (str): ユーザープロンプト
        max_tokens (int, optional): 最大トークン数. デフォルト2000
        temperature (float, optional): 温度パラメータ. デフォルト0.0
        top_p (float, optional): 確率閾値. デフォルト0.9
        max_retries (int, optional): 最大リトライ回数. デフォルト6
        
    Returns:
        str: LLMからの応答テキスト
        
    Raises:
        BedrockClientError: クライアント側のエラー（認証、パラメータ不正など）
        BedrockServiceError: サービス側のエラー（サーバーエラー、タイムアウトなど）
        BedrockError: その他のBedrock関連エラー
    """
    # 1. Bedrockクライアント初期化
    logger.debug("Bedrockクライアントを初期化")
    bedrock = boto3.client(
        service_name='bedrock-runtime',
        region_name='us-east-1',
        config=Config(
            retries=dict(
                max_attempts=0  # 独自のリトライロジックを使用するため0に設定
            )
        )
    )
    
    # 2. リクエストボディ構築
    logger.debug("リクエストボディを構築")
    messages = [
        {
            "role": "user",
            "content": [
                {"text": user_prompt}
            ]
        }
    ]

    # 3. API呼び出し（リトライロジック含む）
    logger.debug(f"API呼び出しを開始 (最大リトライ回数: {max_retries})")
    backoff = 0.5  # 初期バックオフ時間（秒）
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"API呼び出し試行 (試行回数: {attempt + 1})")
            # API呼び出し
            logger.debug("converseを呼び出し")
            response = bedrock.converse(
                modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
                system=[{"text": system_prompt}],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"text": user_prompt}
                        ]
                    }
                ],
                inferenceConfig={
                    "maxTokens": max_tokens,
                    "temperature": temperature,
                    "topP": top_p,
                    "stopSequences": []
                }
            )
            
            # 4. レスポンス解析
            logger.debug("レスポンスの解析を開始")
            logger.debug(f"レスポンス全体: {json.dumps(response, ensure_ascii=False, indent=2)}")
            ai_message = response["output"]["message"]
            if "content" in ai_message and len(ai_message["content"]) > 0:
                response_text = ai_message["content"][0]["text"]
                logger.info("Claude APIからの応答を受信")
                logger.debug(f"応答テキスト長: {len(response_text)}文字")
                return response_text
            logger.warning("空の応答を受信")
            return ""

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            # 4xx系エラー（クライアントエラー）
            if error_code in ['AccessDeniedException', 'ValidationException', 'ResourceNotFoundException']:
                logger.error(f"Bedrock Client Error: {error_code} - {error_message}")
                raise BedrockClientError(f"{error_code}: {error_message}")
            
            # 5xx系エラー（サーバーエラー）
            elif error_code in ['ThrottlingException', 'ServiceUnavailableException', 
                              'ModelTimeoutException', 'ModelNotReadyException']:
                logger.warning(f"Bedrock Service Error (Attempt {attempt + 1}/{max_retries}): {error_code} - {error_message}")
                
                if attempt == max_retries - 1:
                    raise BedrockServiceError(f"Max retries exceeded. Last error: {error_code} - {error_message}")
                
                # 指数バックオフ
                logger.info(f"バックオフ待機: {backoff}秒")
                time.sleep(backoff)
                backoff *= 2.0
                continue
            
            # その他の予期せぬエラー
            else:
                logger.error(f"Unexpected Bedrock Error: {error_code} - {error_message}")
                raise BedrockError(f"Unexpected error: {error_code} - {error_message}")
                
        except Exception as e:
            logger.error(f"Unexpected Error: {str(e)}")
            raise BedrockError(f"Unexpected error: {str(e)}")
    
    raise BedrockServiceError("Max retries exceeded without successful API call")
