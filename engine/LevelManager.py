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
	
	def GetNewID(self):
		# TODO: ask the server for a new Level ID
		for i in xrange(1, 10000):
			if not "level" + str(i) in self.levels.keys():
				return str(i)
	
	def LoadLevel(self, name):
		""" Run on LevelManager init to load all known levels into memory. """
		# TODO: only load on demand
		newlevel = BitLevel(name, self.editLayer)
		newlevel.Load()
		self.levels["level" + name] = newlevel
	
	def NewLevel(self):
		""" Creates a new level. """
		# TODO: proxy this through the server
		id = self.GetNewID()
		newlevel = BitLevel(id, self.editLayer)
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
		# TODO: tell the server the md5 sum of the level we have, and if it's different, it will get downloaded
		if level in self.levels.keys() and (start == "start" or start in self.levels[level].layer.names.keys()):
			self.Remove(self.editLayer)
			if self.level:
				# tell the server we've left this level
				if self.net.serverconnection:
					self.Send({"action": "leavelevel", "id": self.net.playerID})
				if not back:
					# add the source level to the history
					self.AddHistory([self.level, (portal and portal.id) or (self.player.platform and self.player.platform.id) or (self.player.lastplatform and self.player.lastplatform.id) or "start"])
				self.Remove(self.levels[self.level])
				self.levels[self.level].RemovePlayerCamera()
			self.level = level
			# if we're connected already, tell the server (otherwise we'll tell the server when we get the Network_connected callback)
			if self.net.serverconnection:
				self.Send({"action": "setlevel", "id": self.net.playerID, "level": str(self.level)})
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
			self.levels[self.level].SetPlayerCamera(self.player, self.camera, start)
			self.Add(self.levels[self.level])
			self.editLayer.SetLevel(self.levels[level])
			self.Add(self.editLayer)
			self.hud.levelLabel.text = self.levels[self.level].displayName
	
	def AddHistory(self, history):
		if not self.levelHistory or not history == self.levelHistory[-1]:
			self.levelHistory.append(history)
	
	def UnSetLevel(self):
		self.Remove(self.levels[self.level])
		self.levels[self.level].RemovePlayerCamera()
		self.level = None
	
	def SetLevelName(self, name):
		self.levels[self.level].displayName = name
		self.hud.levelLabel.text = name

	###
	### Network events
	###
	
	def Network_playerid(self, data):
		# got my player ID, now send a new level i want to be on
		#self.playerID = data['id']
		self.Send({"action": "setlevel", "id": self.net.playerID, "level": str(self.level)})

