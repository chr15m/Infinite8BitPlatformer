from PodSix.Resource import *
from PodSix.Config import config

class Paintable:
	def __init__(self, editLayer=None):
		self.brushdown = False
		self.editLayer = editLayer
	
	def SetEditLayer(self, editLayer):
		self.editLayer = editLayer
	
	def MouseUp(self, e=None):
		self.brushdown = False
	
	def GetOffset(self, pos):
		rec = [int(r * gfx.width) for r in getattr(self, "rectangle", [0, 0])[:2]]
		return (pos[0] - rec[0], pos[1] - rec[1])
	
	def Paint(self, pos):
		new = self.GetOffset(pos)
		if self.brushdown and self.brushdown != new:
			self.bitmap.Line([self.brushdown, new], self.editLayer.color)
		else:
			#self.bitmap.Pixel(new, self.editLayer.color)
			self.bitmap.Line([new, new], self.editLayer.color)
		self.brushdown = new
	
	def Fill(self, pos, isLevel):
		# if it's a fully transparent level pixel, change the BG
		if isLevel and self.bitmap.Pixel(self.GetOffset(pos))[3] == 0:
			self.bgColor = tuple(self.editLayer.color[:3])
		# otherwise floodfill this sucker
		else:
			self.bitmap.FloodFill(self.GetOffset(pos), self.editLayer.color)

