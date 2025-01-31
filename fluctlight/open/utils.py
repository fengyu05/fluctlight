VISION_INPUT_SUPPORT_TYPE = set(["image/png", "image/jpeg", "image/webp", "image/gif"])
AUDIO_INPUT_SUPPORT_TYPE = set(["audio/ogg", "audio/wav", "audio/mp3"])


def is_o_series_model(model_id: str) -> bool:
    return model_id in ["o1", "o1-mini", "o3", "o3-mini"]


def vision_support_model(model_id: str) -> bool:
    return model_id in ["o1", "o1-mini", "gpt-4o", "gpt-4o-mini"]
