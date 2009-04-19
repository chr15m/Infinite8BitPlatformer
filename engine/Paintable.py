from PodSix.Resource import *
from PodSix.Config import config

class Paintable:
	def Paint(self, pos):
		rec = [int(r * gfx.width) for r in getattr(self, "rectangle", [0, 0])[:2]]
		self.bitmap.Pixel((pos[0] - rec[0], pos[1] - rec[1]), (150, 150, 150, 255))

