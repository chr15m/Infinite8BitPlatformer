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
		self.Send({"server_error": "You don't have a UUID yet!"})
		self.Disconnect()
		self._server.Log("No ID Error! Client %d (%s)" % (self.ID, self.playerID))
	
	##################################
	### Network specific callbacks ###
	##################################
	
	def Network(self, data):
		# called any time data arrives from this client
		# update with this last know update time
		print 'GOT:', data
		self.lastUpdate = time()
	
	def Network_playerid(self, data):
		# client has asked for a new unique, persistent, secret UUID
		# creates the player's unique id and sends it back to them
		# this id is secret and persistent, and not known by any other client
		self.playerID = self._server.GetNewPlayerID(self)
		self.Send({"action": "playerid", "id": self.playerID})
	
	def Network_move(self, data):
		# the player has made some kind of move
		# mirror it to other players in the same level
		# and update our known state
		if data.has_key("id"):
			# tell neighbours what move i just made
			# update my state with what move i just made
 			pass
		else:
			self.NoIDError()
	
	def Network_chat(self, data):
		# this client's player is saying something for others to hear
		if data.has_key("id"):
			# tell neighbours what i just said
			# update my state with what i just said
			pass
		else:
			self.NoIDError()
	
	def Network_setlevel(self, data):
		# the player has entered a particular level
		# send them the state of other players, and the state of other players to them
		if data.has_key("id"):
			if self.level:
				self.SendToNeighbours({"action": "player_leaving"})
			# TODO: stream the lastest version of this level back to the user if they have an out of date copy
			self.level = data['level']
			self.SendToNeighbours({"action": "player_entering"})
			# TODO: send to this player all of the states of the other players in the room
		else:
			self.NoIDError()
	
	def Network_error(self, data):
		print "Error!", data

class I8BPServer(Server):
	# This is an early, quite naive implementation of the game server.
	# It's not secure in any way (e.g. it's very easy to snoop on other people's data, and a bit harder to impersonate them)
	# Don't use this server for serious, important conversations. It's only marginally more secure than email.
	
	# TODO: time-out non-updating clients
	# TODO: make generic disconnect-with-reason method
	# TODO: disconnect clients with the wrong version
	# TODO: disconnect clients who don't have an id but try to do something
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
		# TODO: add this to a pool of known IDs
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

