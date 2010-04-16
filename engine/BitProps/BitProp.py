from PodSix.Resource import *
from PodSix.Config import config
from PodSix.Platformer.Layer import Layer
from PodSix.Rectangle import Rectangle

from engine.Paintable import Paintable
from engine.BitImage import BitImage

class BitProp(Paintable):
	def __init__(self, *args, **kwargs):
		Paintable.__init__(self, kwargs['editLayer'])
		rect = args[0]
		size=(int(rect[2] * gfx.width), int(rect[3] * gfx.width))
		self.bitmap = BitImage(size=size)
		self.bitmap.Fill((255, 0, 255))
		self.box = None
		self.lastDrag = None
		self.levelsize = None
	
	def NewID(self):
		return self.editLayer.MakeId()
	
	def Draw(self):
		if isinstance(self.container, Layer):
			self.box = box = self.container.level.camera.TranslateRectangle(self.rectangle)
			bigmap = self.bitmap.Copy().Scale((box.Width(), box.Height()))
			gfx.BlitImage(bigmap, position=(box[0], box[1]))
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
		self.Constrain()
		self.lastDrag = pos
	
	def Constrain(self):
		if not self.levelsize:
			self.levelsize = tuple([float(x) / gfx.width for x in self.editLayer.level.size])
		
		if self.rectangle.Left() < 0:
			self.rectangle.Left(0)
		if self.rectangle.Top() < 0:
			self.rectangle.Top(0)
		if self.rectangle.Right() > self.levelsize[0]:
			self.rectangle.Right(self.levelsize[0])
		if self.rectangle.Bottom() > self.levelsize[1]:
			self.rectangle.Bottom(self.levelsize[1])
	
	def MouseUp(self, e=None):
		if self.lastDrag:
			self.lastDrag = None
		else:
			Paintable.MouseUp(self)

	def SubImage(self, corner1, corner2):
		"""given two opposite corners of a box, return an image representing the subimage in that box"""
		sub = self.bitmap.Copy()
		sub.RemoveAlpha()
		return sub, [0,0], [self.rectangle.Right(),self.rectangle.Bottom()]
		
	def PasteSubImage(self, image, pos):
		self.bitmap.Blit(image, pos)
			
			
