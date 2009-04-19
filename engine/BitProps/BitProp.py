from PodSix.Resource import *
from PodSix.Config import config
from PodSix.Platformer.Prop import Prop
from PodSix.Platformer.Layer import Layer

from engine.Paintable import Paintable

class BitProp(Paintable):
	editmode = False
	def __init__(self, *args, **kwargs):
		#EventMonitor.__init__(self)
		rect = args[0]
		size=(int(rect[2] * gfx.width), int(rect[3] * gfx.width))
		self.bitmap = Image(size=size, depth=8)
		self.bitmap.surface.set_at((0, 0), (255, 255, 255))
		self.box = None
	
	def Draw(self):
		if isinstance(self.container, Layer):
			self.box = box = self.container.level.camera.TranslateRectangle(self.rectangle)
			gfx.BlitImage(self.bitmap.Copy().Scale((box.Width(), box.Height())), position=(box[0], box[1]))
		else:
			self.box = None	
	
	def DrawEdit(self):
		if self.box:
			gfx.DrawRect(self.box, self.color, 1)
	
	def TestPoint(self, p):
		return  self.rectangle.PointInRect(p)
	
