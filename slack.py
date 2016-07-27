import logging
import os
import pwd
import time
from opsdroid.message import Message
from slackclient import SlackClient

class ConnectorSlack:

    def __init__(self, config):
        """ Setup the connector """
        logging.debug("Loaded slack connector")
        self.token = config["api-token"]
        self.sc = SlackClient(self.token)
        self.name = "slack"

    def connect(self, opsdroid):
        """ Connect to the chat service """
        logging.debug("Connecting to slack")
        if self.sc.rtm_connect():
            while True:
                for m in self.sc.rtm_read():
                    if "type" in m and m["type"] == "message":
                        message = Message(m["text"], m["user"], m["channel"], self)
                        opsdroid.parse(message)
                time.sleep(1)
        else:
            print("Connection Failed, invalid token?")

    def respond(self, message):
        """ Respond with a message """
        logging.debug("Responding with: " + message.message)
        self.sc.api_call(
                "chat.postMessage", channel=message.room, text=message.message,
                username='opsdroid', icon_emoji=':robot_face:'
        )
