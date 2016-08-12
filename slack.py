import logging
import os
import pwd
import time
from opsdroid.message import Message
from slackclient import SlackClient

class ConnectorSlack:

    def __init__(self, config):
        """ Setup the connector """
        logging.debug("Loaded Slack connector")
        self.token = config["api-token"]
        self.sc = SlackClient(self.token)
        self.name = "slack"
        self.bot_name = config["bot-name"]
        self.known_users = {}

    def connect(self, opsdroid):
        """ Connect to the chat service """
        logging.debug("Connecting to Slack")
        if self.sc.rtm_connect():
            logging.info("Connected successfully")
            while True:
                for m in self.sc.rtm_read():
                    if "type" in m and m["type"] == "message" and "user" in m:

                        # Ignore bot messages
                        if "subtype" in m and m["subtype"] == "bot_message":
                            break

                        # Check whether we've already looked up this user
                        if m["user"] in self.known_users:
                            user_info = self.known_users[m["user"]]
                        else:
                            user_info = self.sc.api_call("users.info", user=m["user"])
                            self.known_users[m["user"]] = user_info

                        message = Message(m["text"], user_info["user"]["name"], m["channel"], self)
                        opsdroid.parse(message)
                time.sleep(1)
        else:
            print("Connection Failed, invalid token?")

    def respond(self, message):
        """ Respond with a message """
        logging.debug("Responding with: " + message.text)
        self.sc.api_call(
                "chat.postMessage", channel=message.room, text=message.text,
                username=self.bot_name, icon_emoji=':robot_face:'
        )
