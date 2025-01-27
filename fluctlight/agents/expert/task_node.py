from typing import Any

import structlog
from jinja2 import Template

from fluctlight.agents.expert.data_model import TaskConfig
from fluctlight.constants import GTP_4O_WITH_STRUCT
from fluctlight.open.chat import (
    simple_assistant,
    structure_simple_assistant,
)
from fluctlight.settings import GPT_DEFAULT_MODEL
from fluctlight.task import Task

logger = structlog.getLogger(__name__)


class TaskNode(Task):
    def __init__(self, config: TaskConfig) -> None:
        super().__init__()
        self._config = config
        self.upstream = []

    @property
    def config(self):
        return self._config

    def process(self, *args: Any, **kwds: Any) -> Any:
        inputs = {}
        for key, _type in self.config.input_schema.items():
            inputs[key] = self._require_input(kwargs=kwds, key=key, value_type=_type)

        template = Template(self.config.instruction)
        prompt = template.render(**inputs)

        # output schema is a structure entity
        if self.config.is_structure_output:
            response = structure_simple_assistant(
                model_id=GTP_4O_WITH_STRUCT,
                prompt=prompt,
                output_schema=self.config.output_schema,
            )
        else:
            response = simple_assistant(model_id=GPT_DEFAULT_MODEL, prompt=prompt)
        return response
