summary_prompt = {
    "system_prompt": """
各contentの要点を抽出し、ユーザーに呼びかける口調で、それぞれのtitleを10文字以上20文字以内に要約してください。要約する時に元の文の口調は維持すること。

<output_format>
[{ ghost_id, item_index, summary },...]
</output_format>
""",
    "user_prompt": """{list_of_GhostToneOutputItem}"""
}
