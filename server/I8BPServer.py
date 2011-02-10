from time import sleep, strftime, time
from weakref import WeakKeyDictionary
import sys
from uuid import uuid1
import hashlib
from os import listdir, path as ospath
from json import loads, dumps
from multiprocessing import Process, Queue
from Queue import Empty

from PodSixNet.Server import Server
from PodSixNet.Channel import Channel

# TODO: put these in an external config
# directory containing level update save files
HISTORYDIR = "server/history"
# how often to check for new saves
SAVEINTERVAL = 2
# save after there have been no edits for this long
SAVEAFTER = 30

def RequireID(fn):
	def RequireIDFn(self, data):
		if data.has_key("id") and data['id'] == self.playerID:
			fn(self, data)
		else:
			self.NoIDError()
	return RequireIDFn

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
		self.state["chat"] = []
		self.state["item"] = []
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
		msg.update({"id": self.ID})
		self.AddServerTime(msg)
		# send to all neighbours
		[c.Send(msg) for c in self._server.GetNeighbours(self)]
	
	def AddServerTime(self, d):
		d.update({"servertime": time()})
		return d
	
	def NoIDError(self):
		# this client tried to use the server without having a UUID first
		# we'll tell them and disconnect them and log it
		self.Send({"server_error": "You don't have a UUID yet, or you supplied the wrong UUID."})
		self.Disconnect()
		self._server.Log("No ID Error! Client %d (%s)" % (self.ID, self.playerID))
	
	##################################
	### Network specific callbacks ###
	##################################
	
	def Network(self, data):
		# called any time data arrives from this client
		# update with this last know update time
		#print 'GOT:', data
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
	
	@RequireID
	def Network_edit(self, data):
		# some type of edit action
		# network edits must record the level name where the change was made
		data.update({"level": self.level})
		if self.level:
			editid = self._server.AddLevelHistory(self.level, data)
		self.SendToNeighbours(data)
	
	@RequireID
	def Network_item(self, data):
		data["collected"] = time()
		# the player got an item
		self.SendToNeighbours(data)
		# keep a record of items collected by this player on this level
		self.state["item"].append(data)
		# only remember the last few items collected
		self.state["item"] =  self.state["item"][-5:]
	
	@RequireID
	def Network_move(self, data):
		# the player has made some type of move
		self.SendToNeighbours(data)
		self.state["move"] = data
	
	@RequireID
	def Network_chat(self, data):
		# this client's player is saying something for others to hear
		self.SendToNeighbours(data)
		# add the latest message to the message stack
		self.state["chat"].append(data)
		# make sure we only remember the last few messages
		self.state["chat"] =  self.state["chat"][-5:]
	
	@RequireID
	def Network_haslevel(self, data):
		# tests whether a particular level exists or not and tells this client
		pass
	
	@RequireID
	def Network_setlevel(self, data):
		# the player has entered a particular level
		# send them the state of other players, and the state of other players to them
		if self.level:
			self.SendToNeighbours({"action": "player_leaving"})
		# set the level of this particular client
		self.level = data['level']
		# tell everyone else in the level we are entering
		self.SendToNeighbours({"action": "player_entering"})
		# get a list of changes to this level since we last visited
		changes = self._server.GetLevelHistory(self.level)[data['editid']:]
		# send the 'starting level dump' message
		self.Send(self.AddServerTime({"action": "leveldump", "progress": "start", "size": len(changes)}))
		# send the current history of level changes to the client
		[self.Send(d) for d in changes]
		# tell the client we have finished updating this level so they can end the progress meter and save a copy
		self.Send(self.AddServerTime({"action": "leveldump", "progress": "end", "size": len(changes)}))
		# send to this player all of the states of the other players in the room
		for n in self._server.GetNeighbours(self):
			# tell me about all my neighbours
			self.Send({"action": "player_entering", "id": n.ID, "servertime": time()})
			# tell me about the states of all my neighbours
			for s in n.state:
				if n.state[s]:
					if type(n.state[s]) == type([]):
						for z in n.state[s]:
							state = z.copy()
							state["action"] = s
							self.Send(state)
					else:
						state = n.state[s].copy()
						state["action"] = s
						self.Send(state)
	
	@RequireID
	def Network_leavelevel(self, data):
		if self.level:
			self.SendToNeighbours({"action": "player_leaving"})
			self.level = None
	
	def Network_error(self, data):
		print "Error!", data

class I8BPServer(Server):
	# This is an early, quite naive implementation of the game server.
	# It's not secure in any way (e.g. it's very easy to snoop on other people's data, and a bit harder to impersonate them)
	# Don't use this server for serious, important conversations. It's only marginally more secure than email.
	
	# TODO: disconnect clients with the wrong version
	channelClass = I8BPChannel
	
	def __init__(self, *args, **kwargs):
		Server.__init__(self, *args, **kwargs)
		# list of all currently connected clients
		self.clients = []
		# load all level histories from the json files
		self.levelHistory = self.LoadLevelHistories(HISTORYDIR)
		# when was a level last saved
		self.saved = {}
		self.SetSaved(self.levelHistory.keys())
		# non-secret per-session IDs
		self.ids = 0
		# log the start of the server process
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
	
	def AddLevelHistory(self, level, data):
		""" Add a level edit item to the history of changes of this level. """
		# edit id/index
		if not self.levelHistory.has_key(level):
			self.levelHistory[level] = []
		self.levelHistory[level].append(data)
		data.update({"editid": len(self.levelHistory[level])})
		return len(self.levelHistory[level])
	
	def GetLevelHistory(self, level):
		""" Get the history of changes of this level. """
		if self.levelHistory.has_key(level):
			return self.levelHistory[level]
		else:
			return []
	
	def SetSaved(self, levelnames):
		""" Set a list of levels as saved up to the latest point in history. """
		for l in levelnames:
			self.saved[l] = len(self.levelHistory[l])
	
	def Connected(self, client, addr):
		# Sets the non-uuid non-secret ID for this session
		client.SetID(self.NewSessionID())
		# add this to our pool of known clients
		self.clients.append(client)
		self.Log("Channel %d connected, %d online" % (client.ID, len(self.clients)))
	
	def RemoveClient(self, client):
		self.clients.remove(client)
		self.Log("Channel %d removed, %d left online" % (client.ID, len(self.clients)))
	
	def LoadLevelHistories(self, historydir):
		histories = {}
		for f in listdir(historydir):
			if f.endswith(".json"):
				levelfile = file(ospath.join(historydir, f))
				histories[f[:-len(".json")]] = loads(levelfile.read())
				levelfile.close()
		return histories
	
	def Launch(self):
		lastcheck = 0
		# process for checking for levels to be saved
		p = None
		# queue to communicate with level saving process
		q = Queue()
		q.put("START", block=True)
		while True:
			self.Pump()
			sleep(0.0001)
			# periodically check for unsaved levels with changes and save them
			if lastcheck < time() - SAVEINTERVAL and not q.empty():
				# check if the running process has sent back a list of levels it has saved
				try:
					saved = q.get_nowait()
				except Empty:
					# in rare cases, q.empty() might have returned the wrong answer
					saved = None
				
				# incase q.empty() returned the wrong answer
				if not saved is None:
					# if we actually saved some levels
					if saved != "START":
						# write a log about it
						[self.Log("Saved: " + s) for s in saved]
						# update our last saved array
						self.SetSaved(saved)
					# launch process to save all unsaved levels
					p = Process(target=SaveLevelHistories, args=(q, self.levelHistory, self.saved)).start()
					# update last checked time
					lastcheck = time()

# These run in a separate process/thread

def SaveLevelHistory(levelname, history):
	levelfile = file(ospath.join(HISTORYDIR, levelname) + ".json", "w")
	levelfile.write(dumps(history))
	levelfile.close()
	return levelname

def SaveLevelHistories(q, histories, lastsave):
	# loop through each level and perform a json save if:
	# 	the level has been modified since the last recorded save time
	# 	the last edit was more than X seconds ago
	q.put(
		[SaveLevelHistory(l, histories[l]) 
			for l in histories if 
				lastsave[l] < len(histories[l]) and histories[l][-1]["servertime"] < time() - SAVEAFTER]
		, block=True)

