from PodSix.Platformer.Camera import Camera
from PodSix.ArrayOps import Multiply, Subtract, Add
from PodSix.Resource import *
from PodSix.Config import config
from PodSix.Rectangle import Rectangle

class BitCamera(Camera):
	def TranslateRectangle(self, rectangle):
		rectangle = [int(r) for r in Multiply(rectangle, gfx.width)]
		return Rectangle(Multiply(Subtract(rectangle, Multiply(self.rectangle[:2], gfx.width) + [0, 0]), config.zoom))
	
	def FromScreenCoordinates(self, pos):
		return Add(self.rectangle[:2], Multiply(pos, 1.0 / (gfx.width * config.zoom)))
	
	def ToPixels(self):
		return Rectangle([int(x) for x in Multiply(self.rectangle, gfx.width)])
	
	def PixelOffset(self):
		return [x % 1.0 * config.zoom + 1 for x in Multiply(self.rectangle[:2], gfx.width)]
	
	def CameraToPixels(self):
		return [int(x) for x in Multiply(self.rectangle, gfx.width)]

