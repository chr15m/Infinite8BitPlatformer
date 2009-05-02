from PodSix.Resource import *
from PodSix.Config import config

class Paintable:
	def __init__(self, editLayer=None):
		self.brushdown = False
		self.editLayer = editLayer
	
	def SetEditLayer(self, editLayer):
		self.editLayer = editLayer	
	
	def MouseUp(self):
		self.brushdown = False
	
	def Paint(self, pos):
		rec = [int(r * gfx.width) for r in getattr(self, "rectangle", [0, 0])[:2]]
		new = (pos[0] - rec[0], pos[1] - rec[1])
		if self.brushdown and self.brushdown != new:
			self.bitmap.Line([self.brushdown, new], self.editLayer.color)
		else:
			self.bitmap.Pixel(new, self.editLayer.color)
		self.brushdown = new

