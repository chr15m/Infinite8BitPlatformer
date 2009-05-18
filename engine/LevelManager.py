from os import path, listdir

from simplejson import dumps

from BitLevel import BitLevel

class LevelManager:
	"""
	Manages storage, reading, writing and running of levels.
	"""
	def __init__(self):
		self.levels = {}
		self.level = None
		[self.LoadLevel(x[:-10]) for x in listdir(path.join("resources", "levels")) if x[-10:] == ".level.zip"]
		self.SetLevel("level1", "start")
	
	def LoadLevel(self, name):
		newlevel = BitLevel(name, self.editLayer)
		newlevel.Load()
		self.levels["level" + name] = newlevel
	
	def SetLevel(self, level, start):
		if level in self.levels.keys() and (start == "start" or start in self.levels[level].layer.names.keys()):
			self.Remove(self.editLayer)
			if self.level:
				self.SaveCurrentLevel()
				self.Remove(self.levels[self.level])
				self.levels[self.level].RemovePlayerCamera()
			self.level = level
			self.levels[self.level].SetPlayerCamera(self.player, self.camera, start)
			self.Add(self.levels[self.level])
			self.editLayer.SetLevel(self.levels[level])
			self.Add(self.editLayer)
	
	def UnSetLevel(self):
		self.Remove(self.levels[self.level])
		self.levels[self.level].RemovePlayerCamera()
		self.level = None
	
	def SaveCurrentLevel(self):
		self.levels[self.level].Save()

