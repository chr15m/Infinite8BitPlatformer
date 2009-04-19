from PodSix.Resource import *
from PodSix.Config import config
from PodSix.Platformer.Prop import Prop
from PodSix.Platformer.Layer import Layer

class BitProp(Prop):
	editmode = False
	def __init__(self, *args, **kwargs):
		rect = args[0]
		size=(int(rect[2] * gfx.width), int(rect[3] * gfx.width))
		self.bitmap = Image(size=size, depth=8)
		self.bitmap.surface.set_at((0, 0), (255, 255, 255))
	
	def Draw(self):
		if isinstance(self.container, Layer):
			self.box = box = self.container.level.camera.TranslateRectangle(self.rectangle)
			gfx.BlitImage(self.bitmap.Scale((box.Width(), box.Height())), position=(box[0], box[1]))
		else:
			self.box = None	
	
	def DrawEdit(self):
		if self.box:
			gfx.DrawRect(self.box, self.color, 1)
