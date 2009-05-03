from PodSix.Resource import *
from PodSix.Config import config
from PodSix.Platformer.Prop import Prop
from PodSix.Platformer.Layer import Layer

from engine.Paintable import Paintable

class BitProp(Paintable):
	editmode = False
	def __init__(self, *args, **kwargs):
		Paintable.__init__(self)
		rect = args[0]
		size=(int(rect[2] * gfx.width), int(rect[3] * gfx.width))
		self.bitmap = Image(size=size, depth=8)
		self.bitmap.surface.set_at((0, 0), (255, 255, 255))
		self.box = None
		self.lastDrag = None
	
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
	
	def Drag(self, pos):
		if self.lastDrag:
			self.rectangle.Left(self.rectangle.Left() + (pos[0] - self.lastDrag[0]))
			self.rectangle.Top(self.rectangle.Top() + (pos[1] - self.lastDrag[1]))
		self.lastDrag = pos
	
	def MouseUp(self):
		if self.lastDrag:
			self.lastDrag = None
		else:
			Paintable.MouseUp(self)
