from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase

from core.asgi import application

from .factories import make_post


class BlogSocketTests(TransactionTestCase):
    def test_like_update_is_broadcast_to_post_room(self):
        post = make_post()

        async def scenario():
            communicator = WebsocketCommunicator(application, f"/ws/blog/{post.id}/")
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            await get_channel_layer().group_send(
                f"blog_{post.id}", {"type": "like_update", "likes_count": 7}
            )
            message = await communicator.receive_json_from(timeout=2)
            await communicator.disconnect()
            return message

        message = async_to_sync(scenario)()
        self.assertEqual(message.get("likes_count"), 7)
