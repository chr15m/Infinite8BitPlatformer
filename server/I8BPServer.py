from time import sleep, strftime, time
from weakref import WeakKeyDictionary
import sys
from uuid import uuid1
import hashlib
from os import listdir, path as ospath
from json import loads, dumps
from multiprocessing import Process, Queue
from Queue import Empty
from pprint import pprint
# needed for traceback email handling
import traceback
import cStringIO
import smtplib

from version import VERSION

from PodSixNet.Server import Server
from PodSixNet.Channel import Channel

import settings

def RequireID(fn):
	def RequireIDFn(self, data):
		if data.has_key("id") and data['id'] == self.playerID:
			fn(self, data)
		else:
			self.NoIDError()
	return RequireIDFn

def RequirePermissions(fn):
	def RequirePermissionsFn(self, data):
		if not self.Level().IsLocked() or self.Level().CanEdit(self):
			fn(self, data)
		else:
			self.NoPermissionError()
	return RequirePermissionsFn

def RequireAdmin(fn):
	def RequireAdminFn(self, data):
		if data.has_key("id") and data['id'] == settings.ADMIN_KEY:
			fn(self, data)
		else:
			self.NoAdminError(data)
	return RequireAdminFn

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
		self.state["chat"] = {}
		self.lastUpdate = 0
		Channel.__init__(self, *args, **kwargs)
	
	def Close(self):
		# When the socket is closed, this gets fired
		# tell my neighbours i have left
		self.SendToNeighbours({"action": "player_leaving"})
		self._server.Log('DISCONNECT: Client %d (%s) disconnected' % (self.ID, self.playerID))
		self._server.RemoveClient(self)
	
	def SetID(self, ID):
		# Set's my network ID, unique each time i connect (per session), known to other clients in the same level
		self.ID = ID
		self.Send({"action": "public_id", "public_id": self.ID})
	
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
		self.close_when_done()
		self._server.Log("ERROR: No ID Error! Client %d (%s)" % (self.ID, self.playerID))
	
	def NoPermissionError(self):
		# this client tried to edit a level without having permission to do so
		self.Send({"action": "permission", "permission": "You do not have permission to edit this level."})
		#self.close_when_done()
		self._server.Log("ERROR: Permission error: Client %d (%s)" % (self.ID, self.playerID))
	
	def NoAdminError(self, data):
		# this client tried to do admin actions without permission t do so
		self.Send({"action": "permission", "permission": "You are not admin."})
		self._server.Log("ERROR: Bad admin access: %s" % (str(data)))
	
	# shortcut to get the level object corresponding to my current level
	def Level(self):
		return self._server.Level(self.level)
	
	def Error(self, err):
		self._server.Log("CLENT/SOCKET: error")
		SendExceptionEmail(logger=self._server.Log)
	
	##################################
	### Network specific callbacks ###
	##################################
	
	def Network(self, data):
		# called any time data arrives from this client
		# update with this last know update time
		if "debug" in sys.argv:
			self._server.Log('RECEIVED: ' + str(data))
		self.lastUpdate = time()
	
	def Network_playerid(self, data):
		# either player has supplied their unique player ID, in which case we remember it
		# TODO: check against server's clientData to make sure they supplied a valid ID
		if data.has_key("id"):
			self.playerID = data['id']
		# or client has asked for a new unique, persistent, secret UUID
		# creates the player's unique id and sends it back to them
		# this id is secret and persistent, and not known by any other client
		else:
			self.playerID = self._server.GetNewPlayerID(self)
		# check that the client protocol version is new enough to play with us
		clientversion = data.get('version', -1)
		if clientversion < VERSION:
			self.Send({"action": "badversion", "message": "You are running version %d of the client protocol, but the server is %d." % (clientversion, VERSION), "version": VERSION})
			#self.close_when_done()
			self._server.Log("VERSION MISMATCH: %d / server %d" % (clientversion, VERSION))
		else:
			self._server.Log("VERSION: Player %d has ID %s" % (self.ID, self.playerID))
			self.Send({"action": "playerid", "id": self.playerID, "version": VERSION})
	
	@RequireAdmin
	def Network_console(self, data):
		self._server.Log("ADMIN: Running %s" % data['command'])
		# redirect stdin and sterr for collection
		catchall = cStringIO.StringIO()
		oldstd = [sys.stdout, sys.stderr]
		sys.stdout = catchall
		sys.stderr = catchall
		try:
			exec data['command']
		except:
			traceback.print_exc()
		sys.stdout = oldstd[0]
		sys.stderr = oldstd[1]
		self.Send({"action": "result", "result": catchall.getvalue()})
	
	@RequirePermissions
	@RequireID
	def Network_edit(self, data):
		# TODO: level name change is slightly different, remove the logic from here?
		# add the current level to our data
		data.update({"level": self.level})
		# some type of edit action
		# network edits must record the level name where the change was made
		# check if this is a change to the level's name
		if data['instruction'] == "levelname":
			if not self._server.ChangeLevelName(self.level, data):
				data.update({"action": "badlevelname"})
				# the name was taken, send a message back to this user
				self.Send(self.AddServerTime(data))
				# bail out of this operation if the name was taken
				return None
		# if we currently have a level, add this to our level history
		if self.level:
			editid = self._server.AddLevelHistory(self.level, data)
		# send the changes to any neighbours currently in this level
		self.SendToNeighbours(data)
		# if we need to copy the sender of this edit, do so
		self.Send(self.AddServerTime(data))
	
	@RequireID
	def Network_item(self, data):
		self.SendToNeighbours(self.Level().Collect(data))
	
	@RequireID
	def Network_move(self, data):
		# the player has made some type of move
		self.SendToNeighbours(data)
		self.state["move"] = data
	
	@RequireID
	def Network_chat(self, data):
		data["when"] = time()
		# this client's player is saying something for others to hear
		self.SendToNeighbours(data)
		# add the latest message to the message stack
		self.state["chat"] = data
	
	@RequireID
	def Network_activate(self, data):
		self.SendToNeighbours(data)
	
	@RequirePermissions
	@RequireID
	def Network_lock(self, data):
		self.SendToNeighbours(self.Level().Lock(data))
	
	@RequireID
	def Network_newlevel(self, data):
		# creates a new level on the server side and returns the level ID to the client
		self.Send(self.AddServerTime({"action": "newlevel", "id": self._server.CreateLevel(self)}))
	
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
			self.Send(self.AddServerTime({"action": "player_entering", "id": n.ID}))
			# tell me about the states of all my neighbours
			for s in n.state:
				if n.state[s]:
					if type(n.state[s]) == type([]):
						for z in n.state[s]:
							state = z.copy()
							state["action"] = s
							self.Send(self.AddServerTime(state))
					else:
						state = n.state[s].copy()
						state["action"] = s
						self.Send(self.AddServerTime(state))
		# tell the client we have finished updating this level so they can end the progress meter and save a copy
		self.Send(self.AddServerTime({"action": "playerdump", "progress": "end"}))
		# send to this player all items-collected notices
		for i in self._server.levels[self.level].GetCollectedItems():
			self.Send(self.AddServerTime(i))
		# tell the player whether they are an editor of this level or not
		self.Send(self.AddServerTime({"action": "editor", "editor": self.Level().CanEdit(self), "locked": self.Level().IsLocked()}))
	
	@RequireID
	def Network_leavelevel(self, data):
		if self.level:
			self.SendToNeighbours({"action": "player_leaving"})
			self.level = None
	
	def Network_error(self, data):
		print "Error!", data

class ServerLevel:
	def __init__(self, ID, history=[], name="", owner="", locked=False):
		self.ID = ID
		if not name:
			name = self.ID
		self.locked = locked
		self.owner = owner
		self.name = name
		self.itemsCollected = []
		self.SetHistory(history[:])
	
	def MatchName(self, name):
		return name == self.name
	
	def SetSaved(self):
		self.saved = len(self.history)
	
	def SetName(self, name):
		self.name = name
	
	def SaveIfDue(self):
		if self.saved < len(self.history) and self.history[-1]["servertime"] < time() - settings.SAVEAFTER:
			levelfile = file(ospath.join(settings.HISTORYDIR, "level" + str(self.ID)) + ".json", "w")
			levelfile.write(dumps({
				"name": self.name,
				"history": self.GetHistory(),
				"owner": self.owner,
				"locked": self.locked,
			}))
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
	
	def Collect(self, data):
		data["collected"] = time()
		# keep a record of items collected by this player on this level
		self.itemsCollected.append(data)
		self.PurgeOldCollects()
		return data
	
	def Lock(self, data):
		self.locked = data['locked']
		return data
	
	def GetCollectedItems(self):
		self.PurgeOldCollects()
		return self.itemsCollected
	
	def PurgeOldCollects(self):
		removes = []
		# find any expired item collect notices
		for i in self.itemsCollected:
			if i['collected'] <= time() - settings.ITEMHIDETIME:
				removes.append(i)
		# remove the ones we found
		for r in removes:
			self.itemsCollected.remove(r)
	
	def CanEdit(self, client):
		return client.playerID == self.owner
	
	def IsLocked(self):
		return self.locked

class I8BPServer(Server):
	""" Manages client connections and server side data store. """
	channelClass = I8BPChannel
	
	def __init__(self, *args, **kwargs):
		Server.__init__(self, *args, **kwargs)
		# list of all currently connected clients
		self.clients = []
		# list of all known client IDs
		self.clientData = self.LoadClientData()
		# the highest level ID we know about
		self.lastLevelID = 0
		# load all level histories from the json files
		self.levels = self.LoadLevels()
		self.SetSaved(self.levels.keys())
		# non-secret per-session IDs
		self.ids = 0
		# log the start of the server process
		self.Log('LAUNCH: Infinite8BitPlatformer server listening on ' + ":".join([str(i) for i in kwargs['localaddr']]))
	
	def Log(self, message):
		print strftime("%Y-%m-%d %H:%M:%S") + " [" + str(time()) + "]", message
	
	def DumpLevels(self):
		print "HISTORIES:", pprint([(l, self.levels[l].history) for l in self.levels])
	
	### Player routines ###
	
	def Connected(self, client, addr):
		# Sets the non-uuid non-secret ID for this session
		client.SetID(self.NewSessionID())
		# add this to our pool of known clients
		self.clients.append(client)
		self.Log("CONNECT: Channel %d connected, %d online" % (client.ID, len(self.clients)))
	
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
		# remember all clients we have ever created
		self.clientData[newID] = True
		return newID
	
	def RemoveClient(self, client):
		self.clients.remove(client)
		self.Log("REMOVE: Channel %d removed, %d left online" % (client.ID, len(self.clients)))
	
	def LoadClientData(self):
		clientdatadir = settings.CLIENTDATADIR
		clientdata = {}
		for f in listdir(clientdatadir):
			if f.endswith(".json"):
				self.Log("LOAD CLIENT: " + f)
				clientdatafile = file(ospath.join(clientdatadir, f))
				# json data for the client
				cdata = loads(clientdatafile.read())
				# close the client data file since we no longer need it
				clientdatafile.close()
				# get this client's private ID
				cID = f[:-len(".json")]
				# load up the 
				clientdata[cID] = cdata
		return clientdata
	
	### Level routines ###
	
	def CreateLevel(self, client):
		self.lastLevelID += 1
		levelname = "level" + str(self.lastLevelID)
		self.levels[levelname] = ServerLevel(self.lastLevelID, owner=client.playerID)
		self.Log("NEW: " + levelname)
		return self.lastLevelID
	
	def AddLevelHistory(self, level, data):
		""" Add a level edit command to the history of changes of this level. """
		# edit id/index
		self.levels[level].AddHistory(data)
		data.update({"editid": self.levels[level].GetLastEditID()})
		return self.levels[level].GetLastEditID()
	
	def ChangeLevelName(self, level, data):
		if self.FindLevel(data['name']) is None:
			self.levels[level].SetName(data['name'])
			return True
	
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
	
	def Level(self, name):
		return self.levels[name]
	
	def LoadLevels(self):
		historydir = settings.HISTORYDIR
		levels = {}
		for f in listdir(historydir):
			if f.endswith(".json"):
				self.Log("LOAD LEVEL: " + f)
				levelfile = file(ospath.join(historydir, f))
				# json data for this level
				leveldata = loads(levelfile.read())
				# close off the levelfile since we no longer need it
				levelfile.close()
				# get the level ID number out of the filename
				lID = int(f[len("level"):-len(".json")])
				# create a new level
				levels[f[:-len(".json")]] = ServerLevel(lID, leveldata['history'], leveldata['name'], leveldata['owner'], leveldata['locked'])
				# make sure our highestLevelID is still valid
				if lID > self.lastLevelID:
					self.lastLevelID = lID
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
			if lastcheck < time() - settings.SAVEINTERVAL and not q.empty():
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
						[self.Log("SAVED %s: %s" % s) for s in saved]
						# update our last saved array
						self.SetSaved([s[1] for s in saved if s[0] == "LEVEL"])
					# launch process to save all unsaved levels
					p = Process(target=SaveData, args=(q, self.levels, self.clientData)).start()
					# update last checked time
					lastcheck = time()
			# make sure we don't eat 100% of CPU
			sleep(0.0001)

### Separate thread/process for handling disk IO, emails, etc. ###

def SaveData(q, levels, clientdata):
	# save any unsaved client data/ids
	savedclients = []
	for c in clientdata.keys():
		clientfile = ospath.join(settings.CLIENTDATADIR, c + ".json")
		if not ospath.isfile(clientfile):
			f = file(clientfile, "w")
			f.write(dumps(True))
			f.close()
			savedclients.append(("CLIENT", c))
	# loop through each level and perform a json save if:
	# 	the level has been modified since the last recorded save time
	# 	the last edit was more than X seconds ago
	q.put([("LEVEL", l) for l in levels if levels[l].SaveIfDue()] + savedclients, block=True)

# TODO: put this in it's own module

def SendExceptionEmail(message=None, logger=None):
	def DoLog(msg):
		if logger:
			logger(msg)
		else:
			print msg
	
	# before anything, fetch the exception that was thrown and it's value
	exctype, value = sys.exc_info()[:2]
	
	# ignore ctrl-C
	if exctype == KeyboardInterrupt:
		DoLog("\nEXIT: keyboard interrupt")
		return
	
	if not message:
		# now print the traceback out as per usual
		traceback.print_exc()
		# now catch the actual exception text
		catcherror = cStringIO.StringIO()
		traceback.print_exc(file=catcherror)
		message = catcherror.getvalue()
	
	def DoSend(msg, settings):
		if settings.SERVER_EMAIL_EXCEPTIONS and settings.ADMIN_EMAIL:
			s = None
			# use ssl email if the user specified it
			if settings.EMAIL_USE_SSL:
				s = smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT)
			else:
				s = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
			
			# set up the TLS stuff if specified
			if settings.EMAIL_USE_TLS:
				s.ehlo()
				s.starttls()
				s.ehlo()
			
			# log in if they supplied smtp login details
			if settings.EMAIL_USERNAME:
				s.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
			
			# create the full text of the actual email to sent
			fulltext = (
				"From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" %
				(settings.FROM_EMAIL, settings.ADMIN_EMAIL, "Infinite8BitPlatformerServer crash")
			) + msg
			
			# try to send it, and we're done
			s.sendmail(settings.FROM_EMAIL, [settings.ADMIN_EMAIL], fulltext)
			s.quit()
		
	DoLog("EMAIL: server exception sender launched to email '%s'" % settings.ADMIN_EMAIL)
	
	# launch a new process to perform the actual sending of the email so it doesn't block the server
	Process(target=DoSend, args=(message, settings)).start()

