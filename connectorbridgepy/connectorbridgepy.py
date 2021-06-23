import binascii
import datetime
import json
import logging
import os
import re
import socket
import sys

from Crypto.Cipher import AES
from enum import Enum
from types import SimpleNamespace

_logger = logging.getLogger("connectorbridgepy")

# ConnectorBridge
class ConnectorBridge:

	class DeviceType(Enum):
		BRIDGE = "02000001"
		RADIOMOTOR = "10000000"
		WIFICURTAIN = "22000000"
		WIFIMOTOR = "22000002"
		WIFIRECEIVER = "22000005"

		def description(self):
			switcher = {
				self.BRIDGE: "Wi-Fi Bridge",
				self.RADIOMOTOR: "433Mhz Radio Bi-directional Motor",
				self.WIFICURTAIN: "Wi-Fi Curtain",
				self.WIFIMOTOR: "Wi-Fi tubular motor",
				self.WIFIRECEIVER: "Wi-Fi receiver"
			}
			return switcher.get(self, "Invalid Device Type")


	class DeviceSubType(Enum):
		ROLLERBLINDS = 1
		VENETIANBLINDS = 2 
		ROMANBLINDS = 3
		HONEYCOMBBLINDS = 4
		SHANGRILABLINDS = 5
		ROLLERSHUTTER = 6
		ROLLERGATE = 7
		AWNING = 8
		TBDU = 9
		DAYNIGHTBLINDS = 10
		DIMMINGBLINDS = 11
		CURTAIN = 12
		CURTAINLEFT = 13
		CURTAINRIGHT = 14

		def description(self):
			switcher = {
				self.ROLLERBLINDS: "Roller Blinds",
				self.VENETIANBLINDS: "Venetian Blinds",
				self.ROMANBLINDS: "Roman Blinds",
				self.HONEYCOMBBLINDS: "Honeycomb Blinds",
				self.SHANGRILABLINDS: "Shangri-La Blinds",
				self.ROLLERSHUTTER: "Roller Shutter",
				self.ROLLERGATE: "Roller Gate",
				self.AWNING: "Awning",
				self.TBDU: "TDBU",
				self.DAYNIGHTBLINDS: "Day & Night Blinds",
				self.DIMMINGBLINDS: "Dimming Blinds",
				self.CURTAIN: "Curtain",
				self.CURTAINLEFT: "Curtain (Open Left)",
				self.CURTAINRIGHT: "Curtain (Open Right)"
			}
			return switcher.get(self, "Invalid Device Sub Type")


	class DeviceOperation(Enum):
		CLOSE = 0
		OPEN = 1
		STOP = 2
		STATUS = 3

		def description(self):
			switcher = {
				self.CLOSE: "Close/Down",
	    		self.OPEN: "Open/Up",
	    		self.STOP: "Stop",
	    		self.STATUS: "Status query"
			}
			return switcher.get(self, "Invalid Operation")


	# Current state of device, indicates what limit reached
	class DeviceState(Enum):
		NOLIMIT = 0
		TOPLIMIT = 1
		BOTTOMLIMIT = 2
		LIMIT = 3
		LIMITTHIRD = 4

		def description(self):
			switcher = {
				self.NOLIMIT: "Not limited",
	    		self.TOPLIMIT: "Top limit detected",
	    		self.BOTTOMLIMIT: "Bottom limit detected",
	    		self.LIMIT: "Limits detected",
	    		self.LIMITTHIRD: ": 3rd limit detected"
			}
			return switcher.get(self, "Invalid State")


	class DeviceVoltageMode(Enum):
		AC = 0
		DC = 1

		def description(self):
			switcher = {
				self.AC: "AC Motor",
	    		self.DC: "DC Motor"
			}
			return switcher.get(self, "Invalid Voltage Mode")



	class DeviceWirelessMode(Enum):
		UNIDIRECTION = 0
		BIDIRECTION = 1
		BIDIRECTIONLIMIT = 2
		OTHERS = 3

		def description(self):
			switcher = {
				self.UNIDIRECTION: "Uni-direction",
				self.BIDIRECTION: "Bi-direction",
				self.BIDIRECTIONLIMIT: "Bi-direction (mechanical limits)",
				self.OTHERS: "Others"
			}
			return switcher.get(self, "Invalid Wireless Mode")


	class MessageType(Enum):
		GETDEVICELIST = "GetDeviceList"
		READDEVICE = "ReadDevice"
		WRITEDEVICE = "WriteDevice"


	class Payload:

		def msgID(self):
			now = datetime.datetime.now()
			msgID = now.strftime("%Y%m%d%H%M%S")

			return msgID


	class GetDeviceListPayload(Payload):

		def __init__(self):
			self._msgType = ConnectorBridge.MessageType.GETDEVICELIST.value

		def toJSON(self):
			payload = {
				"msgType": self._msgType,
				"msgID": self.msgID()
			}
			return json.dumps(payload)


	class ReadDevicePayload(Payload):

		def __init__(self, deviceType, mac):
			self._msgType = ConnectorBridge.MessageType.READDEVICE.value
			self._deviceType = deviceType
			self._mac = mac

		def toJSON(self):
			payload = {
				"msgType": self._msgType,
				"msgID": self.msgID(),
				"mac": self._mac,
				"deviceType": self._deviceType
			}
			return json.dumps(payload)


	class WriteDevicePayload(Payload):

		def __init__(self, accessToken, deviceType, mac, data):
			self._msgType = ConnectorBridge.MessageType.WRITEDEVICE.value
			self._accessToken = accessToken
			self._deviceType = deviceType
			self._mac = mac
			self._data = data

		def toJSON(self):
			payload = {
				"msgType": self._msgType,
				"msgID": self.msgID(),
				"AccessToken": self._accessToken,
				"mac": self._mac,
				"deviceType": self._deviceType,
				"data": self._data
			}
			return json.dumps(payload)
		

	# Initialise with the key from Connector app - Settings > About > Tap 4 times
	def __init__(self, key):
		_logger.debug("Init with key: " + key)

		self._key = key


	# Setup - get device list, token and create access token
	def setup(self):
		# self.getDeviceList()
		self.getInfo()
		self.refreshToken()


	# Update the access token
	def refreshToken(self):
		if self._token is None:
			_logger.error("No token retrieved from hub")
			return

		aes = AES.new(self._key, AES.MODE_ECB)
		encryptedToken = aes.encrypt(self._token)

		self._accessToken = binascii.hexlify(encryptedToken).upper().decode()

		_logger.debug(self._accessToken)


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


	# Get the device list from the hub
	def getDeviceList(self):
		# msgID is date/time
		now = datetime.datetime.now()
		msgID = now.strftime("%Y%m%d%H%M%S")

		payload = self.GetDeviceListPayload().toJSON()

		# Send the payload to the hub, and get the reply
		response = self.sendUDP(payload)

		# Update the token for later
		self._token = response["token"]

		# Cache the device list
		self._deviceList = response["data"]

		return response


	# Display information about the hub and connected devices
	def getInfo(self):
		response = self.getDeviceList()

		deviceType = self.DeviceType(response["deviceType"])

		print("Device type: " + deviceType.description())
		print("Firmware version: " + response["fwVersion"])
		print("Protocol version: " + response["ProtocolVersion"])
		print("MAC address: " + response["mac"])

		deviceCount = len(response["data"])

		print("Number of devices: " + str(deviceCount))

		if deviceCount > 0:
			for deviceData in response["data"]:
				deviceType = self.DeviceType(deviceData["deviceType"])
				print("--> Device type: " + deviceType.description() + " MAC: " + deviceData["mac"])


	# Query a single device and show the information
	def getDeviceInfo(self, device):
		response = self.readDevice(device)

		data = response["data"]
		deviceSubType = self.DeviceSubType(data["type"])
		deviceOperation = self.DeviceOperation(data["operation"])
		deviceState	= self.DeviceState(data["currentState"])
		deviceVoltageMode = self.DeviceVoltageMode(data["voltageMode"])
		deviceWirelessMode = self.DeviceWirelessMode(data["wirelessMode"])

		print("Device sub type: " + deviceSubType.description())
		print("Operation: " + deviceOperation.description())
		print("Current position: " + str(data["currentPosition"]))			# 0 - 100
		print("Current angle: " + str(data["currentAngle"]))				# 0 - 180
		print("Current state: " + deviceState.description())
		print("Motor type: " + deviceVoltageMode.description())
		print("Battery level: " + str(data["batteryLevel"]))
		print("Wireless mode: " + deviceWirelessMode.description())
		print("RSSI: " + str(data["RSSI"]))

	# Query a child device current status. Only bi-directional devices supported
	def readDevice(self, device):
		# TODO: Check device is "10000000" or fail

		payload = self.ReadDevicePayload("10000000", device).toJSON()
		return self.sendUDP(payload)


	def sendCommand(self, device, command, value):
		payload = self.WriteDevicePayload(self._accessToken, "10000000", device, {"operation": command.value}).toJSON()
		print(payload)
		self.sendUDP(payload)


def main():
	logging.basicConfig(level=logging.DEBUG)

	print("Example firing")

	connector = ConnectorBridge(key="")

	connector.setup()
	connector.getDeviceInfo("3c71bf6cf5b8000c")
	# connector.sendCommand("3c71bf6cf5b8000c", ConnectorBridge.DeviceOperation.OPEN, 0)
	# connector.getInfo()

if __name__ == "__main__":
    main()