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
	def UDP(self, cmd):
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
		return self.UDP(payload)

	def info(self):
		print (f'{self.colour.purple}'+os.path.basename(__file__)+' [name/all] [open/close/up/down/stop/halt/query/status/shuffle/0-100]')
		# if len(blinds)!=int(len(reply['data']))-1:
		# 	print (f'{colour.red}Warning - Blinds in script  '+str(len(blinds)))
		# 	print ('Warning - Programmed Blinds '+str(len(blinds)-1)+f'{colour.purple}')
		# else:
		# 	print ('Controlled blinds '+str(int(len(reply['data']))-1))
		print ('Firmware version '+str(reply['fwVersion']))
		print ('MAC address '+mac)
		print ('Key '+key)
		print ('Token '+str(reply['token']))

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
	# connector.info()

if __name__ == "__main__":
    main()