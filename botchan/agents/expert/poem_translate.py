from botchan.agents.expert.data_mode import TaskConfig, TaskEntity
from botchan.agents.expert.task_agent import TaskAgent
from botchan.message_intent import MessageIntent
from botchan.slack.data_model.message_event import MessageEvent


class PoemTranslation(TaskEntity):
    source_title: str
    source_lang: str
    source_text: str

    target_lang: str
    target_title: str
    target_text: str


class PoemGrading(TaskEntity):
    rhetroic: int
    phonetics: int
    emotion: int


def create_poems_translation_task_agent() -> TaskAgent:
    return TaskAgent(
        name="Poem translation",
        description="This task translate poem from any source language to tharget lanuage and display them side by side.",
        intent=MessageIntent.TASK,
        task_graph=[
            TaskConfig(
                task_key="poem_translation",
                instruction="Take user input, if input is a peom name, output the information of the poem translate into the user request language. User input: {text}",
                input_schema={"message_event": MessageEvent},
                output_schema=PoemTranslation,
            ),
            TaskConfig(
                task_key="peom_grader",
                instruction="Take a poem translation, grade the target translation 3 score of 1-5 integer of 3 crieteria. Rhetroic, Phonetics, Emotion. \n\n Peom: {poem_translation}",
                input_schema={"peom": PoemTranslation},
                output_schema=PoemGrading,
                upstream = ['poem_translation'],
            ),
        ],
    )