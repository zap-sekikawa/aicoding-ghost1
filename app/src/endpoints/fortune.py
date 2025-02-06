from fastapi import APIRouter, HTTPException
from schema.schema import ClientInput, ClientOutput
from services.create_topics_service import create_topics
from services.parse_logic_data_service import parse_logic_data
from services.ghost_tone_service import get_ghost_tone
from services.summary_service import create_summary
from services.fortune_block_service import split_fortune_items
import time

router = APIRouter()

@router.post("/fortune", response_model=ClientOutput)
async def get_fortune(client_input: ClientInput) -> ClientOutput:
    try:
        # 1. トピックの生成
        start_time = time.time()
        fortune_items = create_topics(client_input)
        # 生成されたトピックの検証
        if not fortune_items or len(fortune_items.items) != 6:
            raise ValueError("トピックの生成に失敗しました。6つのトピックが必要です。")
        print(f"トピック生成処理時間: {time.time() - start_time:.2f}秒")
        
        # 2. ロジックデータの解析
        start_time = time.time()
        logic_data = parse_logic_data(client_input.datetime, client_input.birthday)
        print("=================================")
        print("logic_data: ", logic_data)
        print(f"ロジックデータ解析処理時間: {time.time() - start_time:.2f}秒")
        
        # 3. フォーチュンアイテムの分割
        start_time = time.time()
        fortune_blocks = split_fortune_items(fortune_items, logic_data.ghost_ids)
        print("=================================")
        print("fortune_blocks: ", fortune_blocks)
        print(f"フォーチュンアイテム分割処理時間: {time.time() - start_time:.2f}秒")

        # 4. ゴーストトーンの生成
        start_time = time.time()
        ghost_tone_outputs = []
        for block in fortune_blocks:
            outputs = get_ghost_tone(
                client_input=client_input,
                ghost_id=block.ghost_id,
                fortune_titles=block.fortune_titles,
                logic_data=logic_data
            )
            ghost_tone_outputs.extend(outputs)
        print("=================================")
        print("ghost_tone_outputs: ", ghost_tone_outputs)
        print(f"ゴーストトーン生成処理時間: {time.time() - start_time:.2f}秒")
        
        # 5. 要約の生成
        start_time = time.time()
        summaries = []
        for output in ghost_tone_outputs:
            summary = create_summary(output)
            summaries.append(summary)
        print("=================================")
        print("summaries: ", summaries)
        print(f"要約生成処理時間: {time.time() - start_time:.2f}秒")
        
        return ClientOutput(results=summaries)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
