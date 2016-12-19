import logging
import os
import pwd
import time
import asyncio
import json

import websockets
from slacker import Slacker

from opsdroid.connector import Connector
from opsdroid.message import Message


class ConnectorSlack(Connector):

    def __init__(self, config):
        """ Setup the connector """
        logging.debug("Starting Slack connector")
        self.name = "slack"
        self.config = config
        self.default_room = config.get("default_room", "#general")
        self.token = config["api-token"]
        self.sc = Slacker(self.token)
        self.bot_name = config["bot-name"]
        self.known_users = {}
        self.known_channels = {}
        self.running = False
        self._message_id = 0

    async def connect(self, opsdroid):
        """ Connect to the chat service """
        logging.debug("Connecting to Slack")

        connection = await self.sc.rtm.start()
        self.ws = await websockets.connect(connection.body['url'])
        self.running = True

        self.known_channels = await self.sc.channels.list().body

        # Fix keepalives as long as we're ``running``.
        opsdroid.eventloop.create_task(self.keepalive_websocket())

    async def listen(self, opsdroid):
        """Listen for and parse new messages."""
        while True:
            content = await self.ws.recv()
            m = json.loads(content)
            if "type" in m and m["type"] == "message" and "user" in m:

                # Ignore bot messages
                if "subtype" in m and m["subtype"] == "bot_message":
                    continue

                # Check whether we've already looked up this user
                if m["user"] in self.known_users:
                    user_info = self.known_users[m["user"]]
                else:
                    response = await self.sc.users.info(m["user"])
                    user_info = response.body["user"]
                    if type(user_info) is dict:
                        self.known_users[m["user"]] = user_info
                    else:
                        continue

                message = Message(m["text"], user_info["name"], m["channel"], self)
                await opsdroid.parse(message)

    async def respond(self, message):
        """ Respond with a message """
        logging.debug("Responding with: " + message.text)
        for room in self.known_channels["channels"]:
            if room["name"] == message.room:
                message.room = room["id"]
        await self.sc.chat.post_message(message.room, message.text,
                                        as_user=False, username=self.bot_name,
                                        icon_emoji=':robot_face:')

    async def keepalive_websocket(self):
        while self.running:
            await asyncio.sleep(60)
            await self.ping_websocket()

    async def ping_websocket(self):
        if self.running is False:
            return

        self._message_id += 1
        data = {'id': self._message_id, 'type': 'ping'}
        content = json.dumps(data)
        await self.ws.send(content)
