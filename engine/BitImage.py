from PodSix.Resource import *

class BitImage(Image):
	def __init__(self, *args, **kwargs):
		Image.__init__(self, *args, **kwargs)
		self.surface = self.surface.convert(8)
		self.ResetTransparency()
	
	def ResetTransparency(self):
		self.TransparentColor((255, 0, 255))

