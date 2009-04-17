from os import path

from simplejson import dumps

from BitLevel import BitLevel

class LevelManager:
	"""
	Manages storage, reading, writing and running of levels.
	"""
	def __init__(self):
		self.levels = {}
		self.level = None
		for l in range(3):
			self.LoadLevel(str(l + 1))
		self.SetLevel("level1", "start")
	
	def LoadLevel(self, name):
		newlevel = BitLevel(name)
		#newlevel.LoadSVG(path.join("resources", "level" + name + ".svg"))
		#newlevel.Save()
		newlevel.Load()
		self.levels["level" + name] = newlevel
	
	def SetLevel(self, level, start):
		self.Remove(self.editLayer)
		if self.level:
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

