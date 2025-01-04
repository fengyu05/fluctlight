# import os
import unittest

from fluctlight.agents.expert.shopping_assist import (
    create_shopping_assist_task_graph_agent,
)
from fluctlight.data_model.interface.channel import IChannel
from fluctlight.data_model.interface.message import IMessage
from tests.intergation_test_utils import skip_integration_tests


class TestTaskGraphAgent(unittest.TestCase):
    def setUp(self):
        self.agent = create_shopping_assist_task_graph_agent()

    @skip_integration_tests
    def test_process_message(self):
        msgs = [
            "Hello",
            "Help me buy a shoe",
            "I like the black one",
        ]

        for idx, msg in enumerate(msgs):
            message = IMessage(
                text=msg,
                ts=432432434.4234 + idx,
                message_id=1305047132423721001,
                thread_message_id=1305047132423721001,
                channel=IChannel(id=1302791861341126737, channel_type=IChannel.Type.DM),
                attachments=None,
            )
            responses = self.agent.process_message(
                message=message, message_intent=self.agent.intent
            )
        self.assertEqual(len(responses), 1)
        self.assertEqual(
            responses[0],
            "product_id='shoe_001' quantity='1' spec=name: size\nchoices: ['size_9']",
        )


# Run the tests
if __name__ == "__main__":
    # Set the environment variable
    # os.environ["RUN_INTEGRATION_TESTS"] = "1"
    unittest.main()
