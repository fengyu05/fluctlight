import os
import threading
import time
from contextlib import ExitStack
from pathlib import Path
from typing import cast

import yaml
from langchain.text_splitter import CharacterTextSplitter
from llama_index.core import SimpleDirectoryReader
from readerwriterlock import rwlock

from fluctlight.data_model.interface.character import Character
from fluctlight.database.connection import get_db
from fluctlight.database.models.character import Character as CharacterModel
from fluctlight.embedding.chroma import get_chroma
from fluctlight.logger import get_logger
from fluctlight.settings import (
    CHAR_CATALOG_DIR,
    OVERWRITE_CHROMA,
    CHROMA_DB_COLLECTION_NAME,
)
from fluctlight.utt.singleton import Singleton

logger = get_logger(__name__)


class CatalogManager(Singleton):
    def __init__(self):
        super().__init__()

        self.embedding_db = get_chroma()
        self.sql_db = next(get_db())
        self.sql_load_interval = 30
        self.sql_load_lock = rwlock.RWLockFair()

        if OVERWRITE_CHROMA:
            logger.info("Overwriting existing data in the chroma.")
            self.embedding_db.delete_collection()
            self.embedding_db = get_chroma()

        self.characters: dict[str, Character] = {}
        self.author_name_cache: dict[str, str] = {}
        self.load_characters_from_folder(OVERWRITE_CHROMA)
        if OVERWRITE_CHROMA:
            logger.info("Persisting data in the chroma.")
            self.embedding_db.persist()

        logger.info(
            f"Total document load: {self.embedding_db._client.get_collection(CHROMA_DB_COLLECTION_NAME).count()}"
        )
        self.run_load_sql_db_thread = True
        self.load_sql_db_thread = threading.Thread(target=self.load_sql_db_loop)
        self.load_sql_db_thread.daemon = True
        # self.load_sql_db_thread.start()

    def load_sql_db_loop(self):
        while self.run_load_sql_db_thread:
            self.load_character_from_sql_database()
            time.sleep(self.sql_load_interval)

    def stop_load_sql_db_loop(self):
        self.run_load_sql_db_thread = False

    def get_character(self, character_id: str) -> Character | None:
        with self.sql_load_lock.gen_rlock():
            return self.characters.get(character_id)

    def load_character(self, directory: Path):
        with ExitStack() as stack:
            f_yaml = stack.enter_context(
                open(directory / "config.yaml", encoding="utf8")
            )
            yaml_content = cast(dict, yaml.safe_load(f_yaml))

            character_id = yaml_content["character_id"]
            character_name = yaml_content["character_name"]
            voice_id = yaml_content.get("voice_id", None)
            order = yaml_content.get("order", 10**6)
            self.characters[character_id] = Character(
                character_id=character_id,
                name=character_name,
                llm_system_prompt=yaml_content["system"],
                llm_user_prompt=yaml_content["user"],
                source="local",
                location="repo",
                voice_id=voice_id,
                author_name=yaml_content.get("author_name", "unknown"),
                visibility=yaml_content["visibility"],
                tts=yaml_content.get("text_to_speech_use", None),
                order=order,
                task_config=yaml_content.get("task_config", None),
            )

            return character_name

    def load_data(self, character_name: str, data_path: Path):
        loader = SimpleDirectoryReader(data_path.absolute().as_posix())
        documents = loader.load_data()
        text_splitter = CharacterTextSplitter(
            separator="\n", chunk_size=500, chunk_overlap=100
        )
        docs = text_splitter.create_documents(
            texts=[d.text for d in documents],
            metadatas=[
                {
                    "character_name": character_name,
                    "id": d.id_,
                }
                for d in documents
            ],
        )
        self.embedding_db.add_documents(docs)

    def load_characters_from_folder(self, overwrite: bool):
        """
        Load characters from the character_catalog directory. Use /data to create
        documents and add them to the chroma.

        :param overwrite: if True, overwrite existing data in the chroma.
        """
        if not CHAR_CATALOG_DIR or not os.path.exists(CHAR_CATALOG_DIR):
            logger.warn(
                "CHAR_CATALOG_DIR not configured or does not exist, cannot load character from folder"
            )
            return
        path = Path(CHAR_CATALOG_DIR)
        excluded_dirs = {"archive", "community"}
        directories = [
            d for d in path.iterdir() if d.is_dir() and d.name not in excluded_dirs
        ]
        for directory in directories:
            character_name = self.load_character(directory)
            if character_name and overwrite:
                logger.info("Overwriting data for character: " + character_name)
                self.load_data(character_name, directory / "data")

        logger.info(
            f"Loaded {len(self.characters)} characters: IDs {list(self.characters.keys())}"
        )

    def load_character_from_sql_database(self):
        logger.info("Started loading characters from SQL database")
        character_models = self.sql_db.query(CharacterModel).all()

        with self.sql_load_lock.gen_wlock():
            # delete all characters with location == 'database'
            keys_to_delete = []
            for character_id in self.characters.keys():
                if self.characters[character_id].location == "database":
                    keys_to_delete.append(character_id)
            for key in keys_to_delete:
                del self.characters[key]

            # add all characters from sql database
            for character_model in character_models:
                if character_model.author_id not in self.author_name_cache:
                    author_name = ""
                    self.author_name_cache[character_model.author_id] = author_name  # type: ignore
                else:
                    author_name = self.author_name_cache[character_model.author_id]
                character = Character(
                    character_id=character_model.id,  # type: ignore
                    name=character_model.name,  # type: ignore
                    llm_system_prompt=character_model.system_prompt,  # type: ignore
                    llm_user_prompt=character_model.user_prompt,  # type: ignore
                    source="community",
                    location="database",
                    voice_id=character_model.voice_id,  # type: ignore
                    author_name=author_name,
                    author_id=character_model.author_id,  # type: ignore
                    visibility=character_model.visibility,  # type: ignore
                    tts=character_model.tts,  # type: ignore
                    data=character_model.data,  # type: ignore
                )
                self.characters[character_model.id] = character  # type: ignore
                # TODO: load context data from storage
        logger.info(f"Loaded {len(character_models)} characters from sql database")


def get_catalog_manager() -> CatalogManager:
    return CatalogManager.get_instance()
