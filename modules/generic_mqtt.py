import logging
import random

logger = logging.getLogger(__name__)

class GenericMqtt:
    def __init__(self, config, mqttc):
        self.config = config
        self.mqttc = mqttc

    async def publish(self, **kwargs):
        topic = kwargs["topic"]
        payload = kwargs["payload"]

        logger.info(f"Publishing payload: {payload} to MQTT")
        self.mqttc.publish(topic, payload)
