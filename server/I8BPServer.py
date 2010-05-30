from time import sleep, strftime, time
from weakref import WeakKeyDictionary
import sys
from uuid import uuid1
import hashlib

from PodSixNet.Server import Server
from PodSixNet.Channel import Channel

class I8BPChannel(Channel):
	"""
	This is the server representation of a single connected client.
	"""
	def __init__(self, *args, **kwargs):
		# ID is the non-secret session ID which we share with other connected clients
		self.ID = None
		# player ID is a secret, persistent (across game sessions) uuid only known by this particular client
		self.playerID = None
		# which level this player is currently in
		self.level = None
		# this player's last known state, such as last move performed, position etc.
		self.state = {}
		self.lastUpdate = 0
		Channel.__init__(self, *args, **kwargs)
	
	def Close(self):
		# When the socket is closed, this gets fired
		# tell my neighbours i have left
		self.SendToNeighbours({"action": "player_leaving"})
		self._server.Log('Client %d (%s) disconnected' % (self.ID, self.playerID))
		self._server.RemoveClient(self)
	
	def SetID(self, ID):
		# Set's my network ID, unique each time i connect (per session), known to other clients in the same level
		self.ID = ID
	
	def SendToNeighbours(self, msg):
		# always include my public session ID when sending to my neighbours
		# always include the local server time for this message
		msg.update({"id": self.ID, "servertime": time()})
		# send to all neighbours
		[c.Send(msg) for c in self._server.GetNeighbours(self)]
	
	def NoIDError(self):
		# this client tried to use the server without having a UUID first
		# we'll tell them and disconnect them and log it
		self.Send({"server_error": "You don't have a UUID yet, or you supplied the wrong UUID."})
		self.Disconnect()
		self._server.Log("No ID Error! Client %d (%s)" % (self.ID, self.playerID))
	
	def RebroadcastAndStore(self, data, key):
		# the player has made some kind of move
		if data.has_key("id") and data['id'] == self.playerID:
			# tell neighbours what move i just made
			self.SendToNeighbours(data)
			# update my state with what move i just made
			self.state[key] = data
		else:
			self.NoIDError()
	
	##################################
	### Network specific callbacks ###
	##################################
	
	def Network(self, data):
		# called any time data arrives from this client
		# update with this last know update time
		print 'GOT:', data
		self.lastUpdate = time()
	
	def Network_playerid(self, data):
		# either player has supplied their unique player ID, in which case we remember it
		if data.has_key("id"):
			self.playerID = data['id']
		# or client has asked for a new unique, persistent, secret UUID
		# creates the player's unique id and sends it back to them
		# this id is secret and persistent, and not known by any other client
		else:
			self.playerID = self._server.GetNewPlayerID(self)
			self.Send({"action": "playerid", "id": self.playerID})
	
	def Network_move(self, data):
		# the player has made some type of move
		self.RebroadcastAndStore(data, "move")
	
	def Network_chat(self, data):
		# this client's player is saying something for others to hear
		self.RebroadcastAndStore(data, "chat")
	
	def Network_setlevel(self, data):
		# the player has entered a particular level
		# send them the state of other players, and the state of other players to them
		if data.has_key("id") and data['id'] == self.playerID:
			if self.level:
				self.SendToNeighbours({"action": "player_leaving"})
			# TODO: check the md5 the client sent us and if it's different
			# stream the lastest version of this level back to the user if they have an out of date copy
			self.level = data['level']
			self.SendToNeighbours({"action": "player_entering"})
			# send to this player all of the states of the other players in the room
			for n in self._server.GetNeighbours(self):
				for s in n.state:
					self.Send(n.state[s])
		else:
			self.NoIDError()
	
	def Network_leavelevel(self, data):
		if data.has_key("id") and data['id'] == self.playerID:
			if self.level:
				self.SendToNeighbours({"action": "player_leaving"})
				self.level = None
		else:
			self.NoIDError()
	
	def Network_error(self, data):
		print "Error!", data

class Level:
	""" Each level has an md5 of the zipfile we know about, and an array of other changes which have been applied to that level. """
	def __init__(self, filename=None):
		if filename:
			self.filename = filename
			md5hash = hashlib.md5()
			md5hash.update(file(filename).read())
			self.md5 = md5hash.hexdigest()
		else:
			# create a new unique file with a unique filename
			pass
		self.changes = []
	
	def Save(self, data):
		file(self.filename)
		self.changes = []
		pass

class I8BPServer(Server):
	# This is an early, quite naive implementation of the game server.
	# It's not secure in any way (e.g. it's very easy to snoop on other people's data, and a bit harder to impersonate them)
	# Don't use this server for serious, important conversations. It's only marginally more secure than email.
	
	# TODO: disconnect clients with the wrong version
	channelClass = I8BPChannel
	
	def __init__(self, *args, **kwargs):
		Server.__init__(self, *args, **kwargs)
		self.clients = []
		# non-secret per-session IDs
		self.ids = 0
		self.Log('Infinite8BitPlatformer server listening on ' + ":".join([str(i) for i in kwargs['localaddr']]))
	
	def NewSessionID(self):
		# Gets a new non-secret per-session ID for a new client
		self.ids += 1
		return self.ids
	
	def Log(self, message):
		print strftime("%Y-%m-%d %H:%M:%S") + " [" + str(time()) + "]", message
	
	def GetNeighbours(self, player):
		# returns all other clients who are in the same level as this one, except for itself
		return [c for c in self.clients if c.level == player.level and not c == player]
	
	def GetNewPlayerID(self, channel):
		# make a new secret player ID and add it to our pool
		newID = str(uuid1())
		# TODO: check to make sure no ID gets used twice
		return newID
	
	def Connected(self, client, addr):
		# Sets the non-uuid non-secret ID for this session
		client.SetID(self.NewSessionID())
		# add this to our pool of known clients
		self.clients.append(client)
		self.Log("Channel %d connected, %d online" % (client.ID, len(self.clients)))
	
	def RemoveClient(self, client):
		self.clients.remove(client)
		self.Log("Channel %d removed, %d left online" % (client.ID, len(self.clients)))
	
	def Launch(self):
		while True:
			self.Pump()
			sleep(0.0001)
