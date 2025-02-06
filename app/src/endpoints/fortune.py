from fastapi import APIRouter, HTTPException
from schema.schema import ClientInput, ClientOutput
from services.create_topics_service import create_topics
from services.parse_logic_data_service import parse_logic_data
from services.ghost_tone_service import get_ghost_tone
from services.summary_service import create_summary
from services.fortune_block_service import split_fortune_items

router = APIRouter()

@router.post("/fortune", response_model=ClientOutput)
async def get_fortune(client_input: ClientInput) -> ClientOutput:
    try:
        # 1. トピックの生成
        fortune_items = create_topics(client_input)
        
        # 2. ロジックデータの解析
        logic_data = parse_logic_data()
        
        # 3. フォーチュンアイテムの分割
        fortune_blocks = split_fortune_items(fortune_items, logic_data.ghost_ids)
        
        # 4. ゴーストトーンの生成
        ghost_tone_outputs = []
        for block in fortune_blocks:
            outputs = get_ghost_tone(
                client_input=client_input,
                ghost_id=block.ghost_id,
                fortune_titles=block.fortune_titles,
                logic_data=logic_data
            )
            ghost_tone_outputs.extend(outputs)
        
        # 5. 要約の生成
        summaries = []
        for output in ghost_tone_outputs:
            summary = create_summary(output)
            summaries.append(summary)
        
        return ClientOutput(results=summaries)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
