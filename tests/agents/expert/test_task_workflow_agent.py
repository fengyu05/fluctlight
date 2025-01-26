# import os
import unittest

from fluctlight.agents.expert.shopping_assist import (
    create_shopping_assist_task_graph_agent,
)
from fluctlight.data_model.interface.channel import IChannel
from fluctlight.data_model.interface.message import IMessage
from tests.intergation_test_utils import skip_integration_tests
from fluctlight.logger import get_logger

logger = get_logger(__name__)


class TestTaskWorkflowAgent(unittest.TestCase):
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
            logger.info(f"Responses: {responses}")
            if idx == 1:
                self.assertEqual(len(responses), 1)
                self.assertTrue(
                    responses[0].startswith(
                        "Thanks for being interested in buying shoe."
                    )
                )
            elif idx == 2:
                self.assertEqual(len(responses), 1)
                self.assertTrue(
                    responses[0].startswith(
                        "Based the product match, response to guide user to purchar the product."
                    )
                )

    @skip_integration_tests
    def test_guide_to_buy_product_loop(self):
        msgs = [
            "Hello",
            "Let's talk about whether",
            "Do you know anything about Pokemon?",
            "I want to buy a shoe",
        ]
        for idx, msg in enumerate(msgs):
            message = IMessage(
                text=msg,
                ts=432432434.4234 + idx * 1000,
                message_id=1405047132423721001 + idx * 1000,
                thread_message_id=1405047132423721001,
                channel=IChannel(id=1302791861341126737, channel_type=IChannel.Type.DM),
                attachments=None,
            )
            responses = self.agent.process_message(
                message=message, message_intent=self.agent.intent
            )
            logger.info(f"Responses: {responses}")
            if idx == 3:
                self.assertEqual(len(responses), 1)
                self.assertTrue(
                    responses[0].startswith(
                        "Thanks for being interested in buying shoe."
                    )
                )
            else:
                self.assertEqual(len(responses), 1)
                self.assertFalse(
                    responses[0].startswith(
                        "Thanks for being interested in buying shoe."
                    )
                )


# Run the tests
if __name__ == "__main__":
    # Set the environment variable
    # os.environ["RUN_INTEGRATION_TESTS"] = "1"
    unittest.main()
