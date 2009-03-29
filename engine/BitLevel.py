from os import path

from PodSix.Platformer.Level import Level
from PodSix.Platformer.Layer import Layer
from PodSix.Platformer.Platform import Platform
from PodSix.Platformer.Portal import Portal
from PodSix.Platformer.Item import Item
from PodSix.SVGLoader import SVGLoader

class BitLevel(Level, SVGLoader):
	def __init__(self, name):
		Level.__init__(self, name)
		filename = path.join("resources", self.name + ".svg")
		self.LoadSVG(filename)
	
	def Layer_backgroundboxes(self, element, size, info, dom):
		l = Layer(self)
		for r in self.GetLayerRectangles():
			if r['details'][0] == "portal":
				p = Portal([x / size[0] for x in r['rectangle']], r['id'], r['details'][1])
				l.AddProp(p)
				self.startPoints[r['id']] = p
			elif r['details'][0] == "item":
				p = Item([x / size[0] for x in r['rectangle']], r['id'], r['details'][1])
				l.AddProp(p)
			else:
				p = Platform([x / size[0] for x in r['rectangle']], r['id'])
				l.AddProp(p)
				# platform is a start point
				if len(r['details']) > 1 and r['details'][1] == "start":
					self.startPoints["start"] = p
		
		self.AddLayer(info[1], l)
