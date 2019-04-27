# coding:utf-8
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging
import time
import json
import argparse

# General message notification callback


def subscribeCallback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")


def main():
    # Read in config-file
    f = open("config.json", "r")
    config = json.load(f)
    host = config["host"]
    rootCAPath = config["rootCAPath"]
    certificatePath = config["certificatePath"]
    privateKeyPath = config["privateKeyPath"]
    port = config["port"]
    useWebsocket = config["useWebsocket"]
    clientId = config["clientId"]
    # Library checks type of topic variable and unicode -> str conversion is needed
    topic = str(config["topic"])

    if useWebsocket and certificatePath and privateKeyPath:
        print(
            "X.509 cert authentication and WebSocket are mutual exclusive. Please pick one.")
        exit(2)

    if not useWebsocket and (not certificatePath or not privateKeyPath):
        print("Missing credentials for authentication.")
        exit(2)

    # Port defaults
    if useWebsocket and not port:  # When no port override for WebSocket, default to 443
        port = 443
    if not useWebsocket and not port:  # When no port override for non-WebSocket, default to 8883
        port = 8883

    # Configure logging
    logger = logging.getLogger("AWSIoTPythonSDK.core")
    logger.setLevel(logging.DEBUG)
    streamHandler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    streamHandler.setFormatter(formatter)
    logger.addHandler(streamHandler)

    # Init AWSIoTMQTTClient
    mqCli = None
    if useWebsocket:
        mqCli = AWSIoTMQTTClient(clientId, useWebsocket=True)
        mqCli.configureEndpoint(host, port)
        mqCli.configureCredentials(rootCAPath)
    else:
        mqCli = AWSIoTMQTTClient(clientId)
        mqCli.configureEndpoint(host, port)
        mqCli.configureCredentials(
            rootCAPath, privateKeyPath, certificatePath)

    # AWSIoTMQTTClient connection configuration
    mqCli.configureAutoReconnectBackoffTime(1, 32, 20)
    # Infinite offline Publish queueing
    mqCli.configureOfflinePublishQueueing(-1)
    mqCli.configureDrainingFrequency(2)  # Draining: 2 Hz
    mqCli.configureConnectDisconnectTimeout(10)  # 10 sec
    mqCli.configureMQTTOperationTimeout(5)  # 5 sec

    # Connect and subscribe to AWS IoT
    mqCli.connect()

    # Subscribe to specified topic
    mqCli.subscribe(topic, 1, subscribeCallback)

    while True:
        time.sleep(5)


if __name__ == "__main__":
    main()
