from schema.schema import GhostToneOutputItem, SummaryResult
from utils.llm_client import call_llm
from prompt.summary_prompts import get_summary_prompt

def create_summary(ghost_tone_output: GhostToneOutputItem) -> SummaryResult:
    """
    GhostToneOutputItemの内容を20文字以内に要約する。

    Args:
        ghost_tone_output (GhostToneOutputItem): 要約対象のアドバイス項目

    Returns:
        SummaryResult: 要約結果
    """
    # プロンプトの生成
    prompt = get_summary_prompt(ghost_tone_output)
    
    # LLMの呼び出し
    summary = call_llm(prompt)
    
    # 20文字を超える場合は切り詰める
    summary = summary.strip()
    if len(summary) > 20:
        summary = summary[:20]

    return SummaryResult(
        ghost_id=ghost_tone_output.ghost_id,
        summary=summary,
        content=ghost_tone_output.content
    )
