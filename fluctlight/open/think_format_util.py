def extract_think_message(text: str) -> list[str]:
    """Extract the think message from the response text.
    example:  "<think>abc</think>xyz" => [abc, xyz]

    Args:
        text (str): Input text containing potential think tags

    Returns:
        list[str]: List containing [think_content, remaining_text] or [text] if no think tags
    """
    if "<think>" not in text or "</think>" not in text:
        return [text]

    start_tag = "<think>"
    end_tag = "</think>"

    try:
        start_idx = text.index(start_tag)
        end_idx = text.index(end_tag)

        if start_idx >= end_idx:
            return [text]

        think_content = text[start_idx + len(start_tag) : end_idx]
        remaining_text = text[end_idx + len(end_tag) :]

        return [think_content.strip(), remaining_text.strip()]
    except ValueError:
        return [text]
