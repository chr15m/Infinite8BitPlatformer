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
		# check if this is a change to the level's name
		if data['instruction'] == "levelname":
			self._server.ChangeLevelName(self.level, data)
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
	def Network_newlevel(self, data):
		# creates a new level on the server side and returns the level ID to the client
		self.Send(self.AddServerTime({"action": "newlevel", "id": self._server.CreateLevel()}))
	
	@RequireID
	def Network_haslevel(self, data):
		# checks if a particular level exists
		data.update({"haslevel": self._server.levels.has_key(data['level'])})
		self.Send(self.AddServerTime(data))
	
	@RequireID
	def Network_findlevel(self, data):
		if data.get('name'):
			data.update({"action": "foundlevel", "level": self._server.FindLevel(name=data['name'])})
			self.Send(self.AddServerTime(data))
	
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

class ServerLevel:
	def __init__(self, ID, history=[], name=""):
		self.ID = ID
		if not name:
			name = self.ID
		self.name = name
		self.SetHistory(history)
	
	def MatchName(self, name):
		return name == self.name
	
	def SetSaved(self):
		self.saved = len(self.history)
	
	def SetName(self, name):
		self.name = name
	
	def SaveIfDue(self):
		if self.saved < len(self.history) and self.history[-1]["servertime"] < time() - SAVEAFTER:
			levelfile = file(ospath.join(HISTORYDIR, "level" + str(self.ID)) + ".json", "w")
			levelfile.write(dumps({"name": self.name, "history": self.GetHistory()}))
			levelfile.close()
			return True
	
	def SetHistory(self, history):
		self.history = history
		self.saved = len(history)
	
	def AddHistory(self, data):
		self.history.append(data)
	
	def GetLastEditID(self):
		return len(self.history)
	
	def GetHistory(self):
		return self.history

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
		# the highest level ID we know about
		self.lastLevelID = 0
		# load all level histories from the json files
		self.levels = self.LoadLevels(HISTORYDIR)
		self.SetSaved(self.levels.keys())
		# non-secret per-session IDs
		self.ids = 0
		# log the start of the server process
		self.Log('Infinite8BitPlatformer server listening on ' + ":".join([str(i) for i in kwargs['localaddr']]))
	
	def Log(self, message):
		print strftime("%Y-%m-%d %H:%M:%S") + " [" + str(time()) + "]", message
	
	### Player routines ###
	
	def Connected(self, client, addr):
		# Sets the non-uuid non-secret ID for this session
		client.SetID(self.NewSessionID())
		# add this to our pool of known clients
		self.clients.append(client)
		self.Log("Channel %d connected, %d online" % (client.ID, len(self.clients)))
	
	def NewSessionID(self):
		# Gets a new non-secret per-session ID for a new client
		self.ids += 1
		return self.ids
	
	def GetNeighbours(self, player):
		# returns all other clients who are in the same level as this one, except for itself
		return [c for c in self.clients if c.level == player.level and not c == player]
	
	def GetNewPlayerID(self, channel):
		# make a new secret player ID and add it to our pool
		newID = str(uuid1())
		# TODO: check to make sure no ID gets used twice
		return newID
	
	def RemoveClient(self, client):
		self.clients.remove(client)
		self.Log("Channel %d removed, %d left online" % (client.ID, len(self.clients)))
	
	### Level routines ###
	
	def CreateLevel(self):
		self.lastLevelID += 1
		levelname = "level" + str(self.lastLevelID)
		self.levels[levelname] = ServerLevel(self.lastLevelID)
		self.Log("NEW: " + levelname)
		return self.lastLevelID
	
	def AddLevelHistory(self, level, data):
		""" Add a level edit item to the history of changes of this level. """
		# edit id/index
		self.levels[level].AddHistory(data)
		data.update({"editid": self.levels[level].GetLastEditID()})
		return self.levels[level].GetLastEditID()
	
	def ChangeLevelName(self, level, data):
		self.levels[level].SetName(data['name'])
	
	def GetLevelHistory(self, level):
		""" Get the history of changes of this level. """
		if self.levels.has_key(level):
			return self.levels[level].GetHistory()
		else:
			return []
	
	def SetSaved(self, levelnames):
		""" Set a list of levels as saved up to the latest point in history. """
		for l in levelnames:
			self.levels[l].SetSaved()
	
	def FindLevel(self, name):
		""" Finds a level by it's user visible name. """
		for l in self.levels:
			if self.levels[l].MatchName(name):
				return l
	
	def LoadLevels(self, historydir):
		levels = {}
		for f in listdir(historydir):
			if f.endswith(".json"):
				levelfile = file(ospath.join(historydir, f))
				# json data for this level
				leveldata = loads(levelfile.read())
				# close off the levelfile since we no longer need it
				levelfile.close()
				# get the level ID number out of the filename
				lID = int(f[len("level"):-len(".json")])
				# create a new level
				levels[f[:-len(".json")]] = ServerLevel(lID, leveldata['history'], leveldata['name'])
				# make sure our highestLevelID is still valid
				if lID > self.lastLevelID:
					self.lastLevelID = lID
				self.Log("LOAD: " + f)
		return levels
	
	def Launch(self):
		lastcheck = 0
		# process for checking for levels to be saved
		p = None
		# queue to communicate with level saving process
		q = Queue()
		q.put("START", block=True)
		
		# just keep doing this forever
		while True:
			self.Pump()
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
					p = Process(target=SaveLevelHistories, args=(q, self.levels)).start()
					# update last checked time
					lastcheck = time()
			# make sure we don't eat 100% of CPU
			sleep(0.0001)

# These functions run in a separate process/thread

def SaveLevelHistories(q, levels):
	# loop through each level and perform a json save if:
	# 	the level has been modified since the last recorded save time
	# 	the last edit was more than X seconds ago
	q.put([l for l in levels if levels[l].SaveIfDue()], block=True)

