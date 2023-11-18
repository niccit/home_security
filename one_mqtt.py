# SPDX-License-Identifier: MIT

import json
import ssl
import adafruit_logging
import adafruit_minimqtt.adafruit_minimqtt
import adafruit_minimqtt.adafruit_minimqtt as my_mqtt
import local_logger as logger
from adafruit_io.adafruit_io_errors import AdafruitIO_MQTTError
from adafruit_io.adafruit_io import IO_MQTT


mqtt_prime = None  # The only MQTT client, we don't need multiple
my_log = ""


# Get logging level
try:
    from data import data
except ImportError:
    print("Logging level stored in data.py, please create file")
    raise


# Create or retrieve a MQTT object by name; only retrieves MQTT objects created using this function.
# There can only be one MQTT object; if one already exists it will be returned
# Requires the socketpool name in order to fullyl set up the MQTT client
def getMqtt():
    _addMqtt()
    return mqtt_prime


def _addMqtt():
    global mqtt_prime, my_log

    my_log = logger.getLocalLogger()

    if mqtt_prime is None:
        mqtt_prime = MessageBroker()

        message = "Created MQTT singleton"
        my_log.log_message(message, "info")


# Return properly formatted topic
def get_formatted_topic(feed_name):
    return mqtt_data["username"] + "/feeds/" + feed_name + "/json"


# All the data we need to set up mqtt_client
try:
    from mqtt_data import mqtt_data
except ImportError:
    log_message = "MQTT data stored in mqtt_data.py, please create file"
    my_log.log_message(log_message, "critical")
    raise


# The class where the mqtt_client is initialized
class MessageBroker:

    # Initialize the mqtt_client
    # This method should never be called directly, use getMqtt() instead
    def __init__(self):
        self.mqtt_client = my_mqtt.MQTT(
            broker=mqtt_data["server"],
            port=mqtt_data["port"],
            username=mqtt_data["username"],
            password=mqtt_data["key"],
            is_ssl=True,
            ssl_context=ssl.create_default_context()
        )
        self.io = None
        self.gen_feed = mqtt_data["primary_feed"]
        self.gen_topic = mqtt_data["username"] + "/feeds/" + self.gen_feed + "/json"

    # --- Getters --- #

    # Return self.io
    # If it is none that MQTT is not fully configured
    def get_io(self):
        return self.io

    # --- Methods --- #

    # Configure MQTT to use socketpool
    def configure_publish(self, pool_name):
        my_mqtt.set_socket(pool_name)
        self.io = IO_MQTT(self.mqtt_client)

    # Connect to the MQTT broker
    def connect(self):
        if not self.mqtt_client.is_connected():
            self.io.connect()

    # Subscribe to MQTT topics
    def subscribe(self, topics):
        for t in range(len(topics)):
            topic = mqtt_data["username"] + "/feeds/" + topics[t]
            self.mqtt_client.subscribe(topic)

    # Publish to MQTT
    def publish(self, topic, io_message, log_level: str = "notset", add_sdcard: bool = False):
        if not self.mqtt_client.is_connected():
            my_log.log_message("Need to connect to MQTT", "info")
            self.connect()

        try:
            my_log.add_mqtt_stream(topic)
            my_log.log_message(io_message, log_level, mqtt=True)
        except OSError as oe:
            message = "Unable to publish to MQTT! " + str(oe)
            my_log.log_message(message, "critical")
            pass


