from os import path, listdir

try:
	from json import dumps
except ImportError:
	from simplejson import dumps

from BitLevel import BitLevel

class LevelManager:
	"""
	Manages storage, reading, writing and running of levels.
	"""
	def __init__(self):
		self.levels = {}
		# name of the current level
		self.level = None
		# list of levels the user has visited
		self.levelHistory = []
		[self.LoadLevel(x[:-10]) for x in listdir(path.join("resources", "levels")) if x[-10:] == ".level.zip"]
		self.SetLevel("level1", "start")
		self.newLevelCallback = None
	
	def CurrentLevel(self):
		return self.levels[self.level]
	
	def LoadLevel(self, name):
		""" Run on LevelManager init to load all known levels into memory. """
		# TODO: only load on demand
		newlevel = BitLevel(name, self.editLayer)
		newlevel.Load()
		self.levels["level" + name] = newlevel
	
	def RequestNewLevel(self, callback):
		""" Asks the server to create a new level. """
		self.newLevelCallback = callback
		self.net.SendWithID({"action": "newlevel"})
	
	def NewLocalLevel(self, id):
		""" Makes a new locally cached level object. """
		newlevel = BitLevel(id, self.editLayer)
		newlevel.Initialise()
		self.levels["level" + id] = newlevel
		return newlevel
	
	def SaveLevel(self):
		""" Saves the current level to disk. """
		# TODO: try to upload the level to the server
		if self.level:
			self.levels[self.level].Save()
	
	def Back(self):
		if self.levelHistory:
			# if they haven't moved, skip the destination portal they just teleported to (since they're still standing there)
			if not self.player.lastplatform and len(self.levelHistory) > 1:
				self.levelHistory.pop()
			if self.levelHistory:
				self.SetLevel(back=True, *self.levelHistory.pop())
	
	def SetLevel(self, level, start, portal=None, back=False):
		""" Sets what level the current player is on. """
		if level in self.levels.keys() and (start == "start" or start in self.levels[level].layer.names.keys()):
			self.Remove(self.editLayer)
			if self.level:
				self.LeaveLevel(portal, back)
			self.JoinLevel(level, start)
			# add the edit layer into the entity stack
			self.Add(self.editLayer)
		elif self.net.serverconnection == 1:
			self.Remove(self.editLayer)
			if self.level:
				self.LeaveLevel(portal, back)
			# ask the server whether the level exists
			self.net.SendWithID({"action": "haslevel", "level": str(level), "start": start})
		else:
			self.AddMessage('Sorry, that level does not exist', None, 5.0)
	
	def LeaveLevel(self, portal=None, back=False):
		# tell the server we've left this level
		self.net.SendWithID({"action": "leavelevel"})
		# we don't care about any other players now
		self.players.Clear()
		if not back:
			# add the source level to the history
			self.AddHistory([self.level, (portal and portal.id) or (self.player.platform and self.player.platform.id) or (self.player.lastplatform and self.player.lastplatform.id) or "start"])
		self.Remove(self.levels[self.level])
		# remove the player from the current level
		self.levels[self.level].RemovePlayerCamera()
	
	def JoinLevel(self, level, start=None):
		# set my level to the new level
		self.level = level
		# if we're connected already, tell the server (otherwise we'll tell the server when we get the Network_connected callback)
		self.net.SendWithID({"action": "setlevel", "level": str(self.level), "editid": self.levels[self.level].LastEdit()})
		# send the last move we did to the server
		self.player.SendCurrentMove()
		# add this level to the game
		self.Add(self.levels[self.level])
		# make the level editor aware of this level
		self.editLayer.SetLevel(self.levels[level])
		# set the hud level label to the level name
		self.hud.levelLabel.text = self.levels[self.level].displayName
		if start:
			self.GetOnStart(start)
		else:
			self.levels[self.level].SetCamera(self.camera)
	
	def GetOnStart(self, start):
		# add the destination to the history
		self.AddHistory([self.level, start or "start"])
		# make sure that start actually exists, otherwise find a random portal/platform to jump to
		if start == "start" and not "start" in self.levels[self.level].startPoints.keys() and not "start" in self.levels[self.level].layer.names.keys():
			# try find a random portal
			portals = self.levels[self.level].layer.portals
			if len(portals):
				start = portals[0].id
			else:
				# didn't find a portal, just pick the first platform
				start = self.levels[self.level].layer.platforms[0].id
		# put the camera on the player
		self.levels[self.level].SetPlayerCamera(self.player, self.camera, start)
	
	def AddHistory(self, history):
		if not self.levelHistory or not history == self.levelHistory[-1]:
			self.levelHistory.append(history)
	
	def SetLevelName(self, name):
		self.levels[self.level].displayName = name
		self.hud.levelLabel.text = name
	
	###
	### Network events
	###
	
	def Network_newlevel(self, data):
		newlevel = self.NewLocalLevel(str(data['id']))
		if self.newLevelCallback:
			self.newLevelCallback(newlevel)
			self.newLevelCallback = None
	
	def Network_haslevel(self, data):
		if data['haslevel']:
			# If we are connected make a request to switch level from the server (which will send back a list of changes)
			newlevel = self.NewLocalLevel(data['level'][len("level"):])
			# tell editlayer to send us a note when it has the portal we are looking for
			self.editLayer.SetStartDest(data['start'])
			# actually do the joining of the level (but not the putting on start bit)
			self.JoinLevel(data['level'])
			# add the edit layer into the entity stack
			self.Add(self.editLayer)
		else:
			# TODO: put them back on the same level they were on
			pass
	
	def Network_badlevelname(self, data):
		self.AddMessage('That level name is taken', None, 5.0)

