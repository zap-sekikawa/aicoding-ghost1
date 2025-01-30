from typing import List
import logging
from ..schema.schema import FortuneItems, FortuneBlock

logger = logging.getLogger(__name__)

def split_fortune_items(fortune_items: FortuneItems, ghost_ids: List[int]) -> List[FortuneBlock]:
    logger.info("FortuneItemsの分割処理を開始")
    """
    FortuneItemsをghost_idsの数に応じて分割し、FortuneBlockのリストを生成する
    
    分割ルール:
    - ghost_ids が1つ: [1,2,3,4,5,6] → 1つのブロック
    - ghost_ids が2つ: [1,2,3], [4,5,6] → 2つのブロック
    - ghost_ids が3つ: [1,2], [3,4], [5,6] → 3つのブロック
    - ghost_ids が4つ: [1], [2], [3,4], [5,6] → 4つのブロック
    
    Args:
        fortune_items (FortuneItems): 分割対象のFortuneItems
        ghost_ids (List[int]): 守護霊IDのリスト
        
    Returns:
        List[FortuneBlock]: 分割されたFortuneBlockのリスト
        
    Raises:
        ValueError: ghost_idsが想定外の数の場合やその他のエラー
    """
    try:
        n = len(ghost_ids)  # ユニーク守護霊ID数
        items = fortune_items.items  # 6件
        logger.debug(f"守護霊ID数: {n}, FortuneItems数: {len(items)}")
        
        if len(items) != 6:
            logger.error(f"FortuneItemsの件数が不正: {len(items)}件")
            raise ValueError(f"FortuneItemsは6件である必要があります。現在: {len(items)}件")
        
        # ghost_idsの数に応じて分割方法を決定
        logger.debug("分割方法の決定を開始")
        if n == 1:
            # [0..5] → 全件1ブロック
            block_slices = [(0, 6)]
        elif n == 2:
            # [0..2], [3..5] → 3件ずつ2ブロック
            block_slices = [(0, 3), (3, 6)]
        elif n == 3:
            # [0..1], [2..3], [4..5] → 2件ずつ3ブロック
            block_slices = [(0, 2), (2, 4), (4, 6)]
        elif n == 4:
            # [0..0], [1..1], [2..3], [4..5] → 1,1,2,2件で4ブロック
            block_slices = [(0, 1), (1, 2), (2, 4), (4, 6)]
        else:
            # n > 4は想定外
            error_msg = f"想定外の守護霊ID数です: {n}件"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # 分割実行
        logger.debug("FortuneItemsの分割を実行")
        fortune_blocks = []
        for i, (start, end) in enumerate(block_slices):
            ghost_id = ghost_ids[i]  # i番目のghost_id
            block_items = items[start:end]  # スライスで対象アイテムを取得
            
            fortune_blocks.append(FortuneBlock(
                ghost_id=ghost_id,
                fortune_titles=block_items
            ))
        
        logger.info(f"FortuneItemsの分割処理が完了: {len(fortune_blocks)}ブロックを生成")
        return fortune_blocks
        
    except Exception as e:
        error_msg = f"FortuneItemsの分割処理でエラーが発生: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg)
