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


_LOGGER = logging.getLogger(__name__)


class ConnectorSlack(Connector):

    def __init__(self, config):
        """ Setup the connector """
        _LOGGER.debug("Starting Slack connector")
        self.name = "slack"
        self.config = config
        self.opsdroid = None
        self.default_room = config.get("default-room", "#general")
        self.icon_emoji = config.get("icon-emoji", ':robot_face:')
        self.token = config["api-token"]
        self.sc = Slacker(self.token)
        self.bot_name = config.get("bot-name", 'opsdroid')
        self.known_users = {}
        self.keepalive = None
        self._message_id = 0

    async def connect(self, opsdroid=None):
        """ Connect to the chat service """
        if opsdroid is not None:
            self.opsdroid = opsdroid

        _LOGGER.info("Connecting to Slack")

        try:
            connection = await self.sc.rtm.start()
            self.ws = await websockets.connect(connection.body['url'])

            _LOGGER.debug("Connected as %s", self.bot_name)
            _LOGGER.debug("Using icon %s", self.icon_emoji)
            _LOGGER.debug("Default room is %s", self.default_room)
            _LOGGER.info("Connected successfully")

            if self.keepalive is None or self.keepalive.done():
                self.keepalive = self.opsdroid.eventloop.create_task(
                                                self.keepalive_websocket())
        except aiohttp.errors.ClientOSError as e:
            _LOGGER.error(e)
            _LOGGER.error("Failed to connect to Slack, retrying in 10")
            await self.reconnect(10)

    async def reconnect(self, delay=None):
        """Reconnect to the websocket."""
        if delay is not None:
            await asyncio.sleep(delay)
        await self.connect()

    async def listen(self, opsdroid):
        """Listen for and parse new messages."""
        while True:
            try:
                content = await self.ws.recv()
            except websockets.exceptions.ConnectionClosed:
                _LOGGER.info("Slack websocket closed, awaiting reconnect...")
                await asyncio.sleep(5)
                continue
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
        _LOGGER.debug("Responding with: '" + message.text +
                      "' in room " + message.room)
        await self.sc.chat.post_message(message.room, message.text,
                                        as_user=False, username=self.bot_name,
                                        icon_emoji=self.icon_emoji)

    async def keepalive_websocket(self):
        while True:
            await asyncio.sleep(60)
            self._message_id += 1
            try:
                await self.ws.send(
                    json.dumps({'id': self._message_id, 'type': 'ping'}))
            except (websockets.exceptions.InvalidState, aiohttp.errors.ClientOSError):
                _LOGGER.info("Slack websocket closed, reconnecting...")
                await self.reconnect()
