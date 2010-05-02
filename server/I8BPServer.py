from time import sleep, strftime, time
from weakref import WeakKeyDictionary
import sys
from uuid import uuid1

from PodSixNet.Server import Server
from PodSixNet.Channel import Channel

class I8BPChannel(Channel):
	"""
	This is the server representation of a single connected client.
	"""
	def __init__(self, *args, **kwargs):
		self.ID = None
		self.playerID = None
		Channel.__init__(self, *args, **kwargs)
	
	def Close(self):
		self._server.Log('Client %d disconnected' % self.ID)
	
	def SetID(self, ID):
		self.ID = ID
	
	##################################
	### Network specific callbacks ###
	##################################
	
	def Network_playerid(self, data):
		# creates the player's unique id and sends it back to them
		self.Send({"action": "playerid", "id": self._server.GetNewPlayerID(self)})
	
	def Network_move(self, data):
		# the player has made some kind of move
		# mirror it to other players in the same level
		if data.has_key("id"):
 			pass
	
	def Netork_setlevel(self, data):
		# the player has entered a particular level
		# send them the state of other players, and the state of other players to them
		if data.has_key("id"):
 			pass

class I8BPServer(Server):
	channelClass = I8BPChannel
	
	def __init__(self, *args, **kwargs):
		Server.__init__(self, *args, **kwargs)
		self.channels = []
		self.Log('Infinite8BitPlatformer server listening on ' + ":".join([str(i) for i in kwargs['localaddr']]))
	
	def Log(self, message):
		print strftime("%Y-%m-%d %H:%M:%S") + " [" + str(time()) + "]", message
	
	def GetNewPlayerID(self, channel):
		# make a new player Id and add it to our pool
		newID = str(uuid1())
		# TODO: add this to our pool of IDs
		# TODO: add the new UUID to the database so it doesn't get used again
		return newID
	
	def Connected(self, channel, addr):
		self.channels.append(channel)
		channel.SetID(self.channels.index(channel))
		self.Log("Channel %d connected" % channel.ID)
	
	def Launch(self):
		while True:
			self.Pump()
			sleep(0.0001)

