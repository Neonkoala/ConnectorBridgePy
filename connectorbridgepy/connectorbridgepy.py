import binascii
import datetime
import json
import logging
import os
import re
import socket
import sys

from Crypto.Cipher import AES

_logger = logging.getLogger("connectorbridgepy")

# ConnectorBridge
class ConnectorBridge:

	class Payload:

		def __init__(self, msgType):
			self._msgType = msgType

		def msgID(self):
			now = datetime.datetime.now()
			msgID = now.strftime("%Y%m%d%H%M%S")

			return msgID

		def toJSON(self):
			payload = {
				"msgType": self._msgType,
				"msgID": self.msgID()
			}
			return json.dumps(payload)

	# Initialise with the key from Connector app - Settings > About > Tap 4 times
	def __init__(self, key):
		_logger.debug("Init with key: " + key)

		self._key = key

	# This displays the payload sent to the hub and the JSON reply
	def DEBUG(pld,rpy):
	    print (f"{colour.yellow}PAYLOAD{colour.green}")
	    print (json.dumps(json.loads(pld),indent=3))
	    print (f"{colour.yellow}REPLY{colour.green}")
	    print (json.dumps(rpy,indent=3))

	# Create the UDP socket and send the payload
	# Timeout is set to one second and will stop if no reply received
	# This returns the JSON formatted data from the hub
	def sendUDP(self, cmd):
		bytes = cmd.encode()

		try:
		    udpSocket = socket.socket(family=socket.AF_INET,type=socket.SOCK_DGRAM)
		    udpSocket.settimeout(3)
		    udpSocket.sendto(bytes, ("238.0.0.18",32100))

		    udpResponse = udpSocket.recvfrom(1024)[0]
		    udpString = format(udpResponse.decode("utf-8"))

		    deviceList = json.loads(udpString)

		    udpSocket.close()

		    return(deviceList)
		except socket.timeout:
		    udpSocket.close()
		    _logger.error("Hub is not responding")

	def getDeviceList(self):
		# msgID is date/time
		now = datetime.datetime.now()
		msgID = now.strftime("%Y%m%d%H%M%S")

		payload = self.Payload("GetDeviceList").toJSON()

		# Send the payload to the hub, and get the reply
		response = self.sendUDP(payload)

		# Update the token for later
		self._token = response["token"]

		return response

	def getInfo(self):
		response = self.getDeviceList()

		print("Device type: " + response["deviceType"])
		print("Firmware version: " + response["fwVersion"])
		print("Protocol version: " + response["ProtocolVersion"])
		print("MAC address: " + response["mac"])

		deviceCount = len(response["data"])

		print("Number of devices: " + str(deviceCount))

		if deviceCount > 0:
			for deviceData in response["data"]:
				print("--> Device type: " + deviceData["deviceType"] + " MAC: " + deviceData["mac"])

	def test(self):
		_logger.debug("Test output: " + self._key)
		print(self._key)

		response = self.getDeviceList()

		print(response)

def main():
	logging.basicConfig(level=logging.DEBUG)

	print("Example firing")

	connector = ConnectorBridge(key="")

	connector.test()
	connector.getInfo()

if __name__ == "__main__":
    main()