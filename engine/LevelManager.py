from os import path, listdir

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
		for i in xrange(1, 10000):
			if not "level" + str(i) in self.levels.keys():
				return str(i)
	
	def LoadLevel(self, name):
		newlevel = BitLevel(name, self.editLayer)
		newlevel.Load()
		self.levels["level" + name] = newlevel
	
	def NewLevel(self):
		id = self.GetNewID()
		newlevel = BitLevel(id, self.editLayer)
		self.levels["level" + id] = newlevel
		return newlevel
	
	def SaveLevel(self):
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
		if level in self.levels.keys() and (start == "start" or start in self.levels[level].layer.names.keys()):
			self.Remove(self.editLayer)
			if self.level:
				if not back:
					# add the source level to the history
					self.AddHistory([self.level, (portal and portal.id) or (self.player.platform and self.player.platform.id) or (self.player.lastplatform and self.player.lastplatform.id) or "start"])
				self.Remove(self.levels[self.level])
				self.levels[self.level].RemovePlayerCamera()
			self.level = level
			# add the destination to the history
			self.AddHistory([self.level, start or "start"])
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

