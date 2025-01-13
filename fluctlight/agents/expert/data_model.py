from typing import Any, Callable, Optional, Type, Union

from pydantic import BaseModel


class TaskEntity(BaseModel):
    def __repr__(self):
        field_strings = [f"{key}: {value}" for key, value in self.model_dump().items()]
        return "\n".join(field_strings)

    @classmethod
    def check_nested_field_in_class(cls, field_path: str) -> bool:
        """
        Check whether a nested field path like "a.b" or "a.b.c" exists in this Pydantic class.

        Args:
            field_path (str): The dot-separated path of the field.

        Returns:
            bool: True if the field path exists, False otherwise.
        """
        fields = field_path.split(".")
        current_model: Any = cls
        try:
            for field in fields:
                current_model = current_model.__annotations__[field]
            return True
        except KeyError:
            return False


class IntakeMessage(TaskEntity):
    text: str


class IntakeHistoryMessage(TaskEntity):
    messages: list[str] = []

    @property
    def to_chat_history(self) -> str:
        return "\n".join(self.messages)


class TaskConfig(BaseModel):
    task_key: str
    instruction: str
    input_schema: dict[str, Type[TaskEntity]]  # map from input name to input type
    output_schema: Union[Type[str], Type[TaskEntity]]
    success_criteria: Optional[Callable] = None
    loop_message: Optional[str] = None

    def __repr__(self) -> str:
        field_strings = [f"{key}: {value}" for key, value in self.model_dump().items()]
        return "\n".join(field_strings)

    @property
    def is_root(self) -> bool:
        """Root node is node only has intake Message"""
        return [IntakeMessage] == list(self.input_schema.values())

    @property
    def is_structure_output(self) -> bool:
        return issubclass(self.output_schema, TaskEntity)
