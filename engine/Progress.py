import os

from PodSix.Resource import *

from PodSix.Concurrent import Concurrent

class Progress(Concurrent):
	def __init__(self):
		Concurrent.__init__(self)
		self.sprite = Image(file=os.path.join("resources", "progress.png"))
		self.showing = False
		self.maximum = 1
		self.value = 0
		self.width = 142
		self.height = 20
		self.priority = 5
	
	def Draw(self):
		if self.showing:
			gfx.screen.fill([80, 80, 80], special_flags=BLEND_SUB)
			gfx.BlitImage(self.sprite, center=[gfx.width / 2, gfx.height / 2])
			gfx.DrawRect((gfx.width / 2 - self.width / 2, gfx.height / 2 - self.height / 2, self.width * (1 - float(self.value) / self.maximum), self.height), [255, 0, 0], 0)
	
	def Show(self, maximum=None):
		if not maximum is None:
			self.maximum = maximum
		self.showing = True
	
	def Hide(self):
		if self.showing:
			self.showing = False
	
	def Value(self, val, maximum=None):
		if not maximum is None:
			self.maximum = maximum
		self.value = val

