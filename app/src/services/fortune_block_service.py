from typing import List
from schema.schema import FortuneItems, FortuneBlock, FortuneItem

def split_fortune_items(fortune_items: FortuneItems, ghost_ids: List[int]) -> List[FortuneBlock]:
    """
    FortuneItemsをghost_idsに基づいて分割し、FortuneBlockのリストを生成する。

    Args:
        fortune_items (FortuneItems): 分割対象のFortuneItems
        ghost_ids (List[int]): 守護霊IDのリスト

    Returns:
        List[FortuneBlock]: 分割されたFortuneBlockのリスト
    """
    # ghost_idsの数に基づいて、各ブロックに含めるアイテム数を計算
    total_items = len(fortune_items.items)
    num_ghosts = len(ghost_ids)
    base_items_per_ghost = total_items // num_ghosts
    remainder = total_items % num_ghosts

    # FortuneBlockのリストを生成
    blocks: List[FortuneBlock] = []
    current_index = 0

    for i, ghost_id in enumerate(ghost_ids):
        # このゴーストに割り当てるアイテム数を計算
        items_for_this_ghost = base_items_per_ghost
        if i < remainder:
            items_for_this_ghost += 1

        # このゴーストのアイテムを取得
        ghost_items = fortune_items.items[current_index:current_index + items_for_this_ghost]
        
        # FortuneBlockを作成
        block = FortuneBlock(
            ghost_id=ghost_id,
            fortune_titles=ghost_items
        )
        blocks.append(block)

        current_index += items_for_this_ghost

    return blocks
