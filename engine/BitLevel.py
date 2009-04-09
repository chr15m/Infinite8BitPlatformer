from os import path

from PodSix.Platformer.Level import Level
from PodSix.Platformer.Layer import Layer
from PodSix.Platformer.Platform import Platform
from PodSix.Platformer.Portal import Portal
from PodSix.Platformer.Item import Item
from PodSix.Platformer.Prop import Prop
from PodSix.SVGLoader import SVGLoader
from PodSix.Resource import *
from PodSix.Config import config

def PropDraw(self):
	if isinstance(self.container, Layer):
		gfx.DrawRect(self.container.level.camera.TranslateRectangle(self.rectangle), self.color, 1)

Prop.Draw = PropDraw

Platform.color = [255, 255, 255]
Portal.color = [255, 0, 0]
Item.color = [255, 255, 0]

class BitLevel(Level, SVGLoader):
	def __init__(self, name):
		Level.__init__(self, name)
		self.layer = Layer(self)
		self.bitmap = {}
		filename = path.join("resources", self.name + ".svg")
		self.LoadSVG(filename)
		self.gravity = self.gravity / config.zoom
	
	def Layer_backgroundboxes(self, element, size, info, dom):
		l = self.layer
		for r in self.GetLayerRectangles():
			if r['details'][0] == "portal":
				p = Portal([int(x / config.zoom) / size[0] for x in r['rectangle']], r['id'], r['details'][1])
				l.AddProp(p)
				self.startPoints[r['id']] = p
			elif r['details'][0] == "item":
				p = Item([int(x / config.zoom) / size[0] for x in r['rectangle']], r['id'], r['details'][1])
				l.AddProp(p)
			else:
				p = Platform([int(x / config.zoom) / size[0] for x in r['rectangle']], r['id'])
				l.AddProp(p)
				# platform is a start point
				if len(r['details']) > 1 and r['details'][1] == "start":
					self.startPoints["start"] = p
		
		self.AddLayer(info[1], l)
	
	def AddPlatform(self, coords):
		return self.layer.AddProp(Platform(coords))
	
