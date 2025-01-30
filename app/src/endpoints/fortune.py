from fastapi import APIRouter, HTTPException, status
from ..schema.schema import ClientInput, ClientOutput
from ..services.create_topics_service import create_topics
from ..services.parse_logic_data_service import parse_logic_data
from ..services.ghost_tone_service import ghost_tone_model
from ..services.summary_service import summary_model
from ..services.fortune_block_service import split_fortune_items
from ..data.default_topics import DEFAULT_TOPICS as default_fortune_items
from ..repository.mock_repository import MockRepository  # or external_repository
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/fortune", response_model=ClientOutput)
async def get_fortune(client_input: ClientInput):
    """
    運勢を取得するエンドポイント
    
    Args:
        client_input (ClientInput): クライアントからの入力データ
        
    Returns:
        ClientOutput: 運勢結果のレスポンス
    """

    """
    運勢を取得するエンドポイント
    
    Args:
        client_input (ClientInput): クライアントからの入力データ
        
    Returns:
        ClientOutput: 運勢結果のレスポンス
        
    Raises:
        HTTPException: 処理中にエラーが発生した場合
    """
    try:
        logger.info(f"リクエスト受信: {client_input}")
        
        # 1. 閲覧履歴取得
        browsing_history = client_input.browsing_history
        logger.debug(f"閲覧履歴: {browsing_history}")

        # 2. create_topics or default_topics
        try:
            if len(browsing_history) == 0:
                logger.info("閲覧履歴なし: デフォルトトピックを使用")
                fortune_items = default_fortune_items
            else:
                logger.info("閲覧履歴あり: トピック生成開始")
                fortune_items = create_topics(browsing_history)
                logger.debug(f"生成されたトピック: {fortune_items}")
        except Exception as e:
            logger.error(f"トピック生成エラー: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="トピック生成中にエラーが発生しました"
            )

        # 3. ロジックデータ取得
        try:
            repository = MockRepository()
            logic_data_xml = repository.get_logic_data()
            logic_data = parse_logic_data(logic_data_xml)
            logger.debug(f"取得したロジックデータ: {logic_data}")
        except Exception as e:
            logger.error(f"ロジックデータ取得/パースエラー: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ロジックデータの取得中にエラーが発生しました"
            )

        # 4. FortuneBlock分割
        try:
            fortune_blocks = split_fortune_items(fortune_items, logic_data.ghost_ids)
            logger.debug(f"分割されたフォーチュンブロック: {fortune_blocks}")
        except Exception as e:
            logger.error(f"フォーチュンブロック分割エラー: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="フォーチュンブロックの分割中にエラーが発生しました"
            )

        # 5. ghost_tone_model呼び出し
        try:
            ghost_tone_results = ghost_tone_model(
                fortune_blocks, 
                logic_data, 
                has_browsing_history=(len(browsing_history)>0)
            )
            logger.debug(f"ゴーストトーン結果: {ghost_tone_results}")
        except Exception as e:
            logger.error(f"ゴーストトーンモデルエラー: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ゴーストトーンの生成中にエラーが発生しました"
            )

        # 6. summary_model呼び出し
        try:
            summary_results = summary_model(ghost_tone_results)
            logger.debug(f"サマリー結果: {summary_results}")
        except Exception as e:
            logger.error(f"サマリーモデルエラー: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="サマリーの生成中にエラーが発生しました"
            )

        # 7. 出力成形
        output = ClientOutput(results=summary_results)
        logger.info("レスポンス生成完了")
        return output

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"予期せぬエラーが発生: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="予期せぬエラーが発生しました"
        )
