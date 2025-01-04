from typing import Any
from pydantic import BaseModel


class Character(BaseModel):
    character_id: str
    name: str
    llm_system_prompt: str
    llm_user_prompt: str
    source: str = ""
    location: str = ""
    voice_id: str | None = None
    author_name: str = ""
    author_id: str = ""
    visibility: str = ""
    tts: str | None = None
    order: int = 10**9  # display order on the website
    data: dict | None = None
    task_config: dict[str, Any] | None = None


class CharacterRequest(BaseModel):
    name: str
    system_prompt: str | None = None
    user_prompt: str | None = None
    tts: str | None = None
    voice_id: str | None = None
    visibility: str | None = None
    data: dict | None = None
    avatar_id: str | None = None
    background_text: str | None = None


class EditCharacterRequest(BaseModel):
    id: str
    name: str | None = None
    system_prompt: str | None = None
    user_prompt: str | None = None
    tts: str | None = None
    voice_id: str | None = None
    visibility: str | None = None
    data: dict | None = None
    avatar_id: str | None = None
    background_text: str | None = None


class DeleteCharacterRequest(BaseModel):
    character_id: str
