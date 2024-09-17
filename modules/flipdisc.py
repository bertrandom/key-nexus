import logging
import random

logger = logging.getLogger(__name__)

class FlipDisc:
    def __init__(self, config, mqttc):
        self.config = config
        self.mqttc = mqttc

    async def displayWord(self, **kwargs):
        word = kwargs["word"]

        logger.info(f"Publishing word: {word} to MQTT")
        self.mqttc.publish("iot/flipdisc", word)

    async def displayRandomWord(self):
        # Path to the file
        file_path = '/web/push-four/aurora_words.txt'

        # Read the file and pick a random line
        with open(file_path, 'r') as file:
            words = file.readlines()  # Read all lines from the file

        # Pick a random word from the list (removing the newline character if present)
        word = random.choice(words).rstrip('\n')

        logger.info(f"Publishing word: {word} to MQTT")
        self.mqttc.publish("iot/flipdisc", word)