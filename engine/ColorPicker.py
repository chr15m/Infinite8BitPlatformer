from os import path

from PodSix.Resource import *
from PodSix.Concurrent import Concurrent

import palettes

class ColorPicker(Concurrent, EventMonitor):
	def __init__(self, parent):
		Concurrent.__init__(self)
		EventMonitor.__init__(self)
		self.parent = parent
		self.bitmaps = {}
		for x in palettes.all.keys():
			bm = Image(path.join("resources", "palettes", x + ".png"))
			bm.Scale([s * 8 for s in bm.Size()])
			self.bitmaps[x] = bm
		self.bm = bm
		self.triggered = False
	
	def Pump(self):
		self.triggered = False
		Concurrent.Pump(self)
		EventMonitor.Pump(self)	
	
	def MouseDown(self, e):
		sz = self.bm.Size()
		if e.pos[0] > gfx.width - (sz[0] + 16) and e.pos[1] > gfx.height - sz[1]: 
			if e.pos[0] > gfx.width - sz[0]:
				self.parent.color = self.bm.Pixel((e.pos[0] - gfx.width + sz[0], e.pos[1] - gfx.height + sz[1]))
				self.triggered = True
			elif e.pos[1] > gfx.height - 16:
				self.parent.color = (255, 0, 255, 0)
				self.triggered = True
	
	def Draw(self):
		self.bm = self.bitmaps[self.parent.level.palette]
		sz = self.bm.Size()
		gfx.BlitImage(self.bm, position=(gfx.width - sz[0], gfx.height - sz[1]))
		gfx.DrawRect([gfx.width - sz[0] - 1, gfx.height - 1, -16, -16], (255, 0, 255), 1)

