from os import path

from simplejson import dumps, loads

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

Platform.color = [255, 255, 255]
Portal.color = [255, 0, 0]
Item.color = [255, 255, 0]

class BitLevel(Level, SVGLoader):
	def __init__(self, name):
		Level.__init__(self, name)
		self.basefilename = path.join("resources", "levels", self.name)
		self.layer = Layer(self)
		self.bitmap = {}
		self.gravity = self.gravity / config.zoom
		self.backgroundColor = (15, 15, 15)
		self.bitmap = Image(size=(1024, 1024), depth=8)
		self.history = []
	
	###
	###	UI/Bitmap routines
	###
	
	def Draw(self):
		gfx.SetBackgroundColor(self.backgroundColor)
		subPixOffset = self.camera.PixelOffset()
		pixelBoxSize = self.camera.ToPixels().Grow(1, 1)
		box = pixelBoxSize.Clip([0, 0, 1024, 1024])
		gfx.BlitImage(self.bitmap.SubImage(box).Scale((box.Width() * config.zoom, box.Height() * config.zoom)), position=(-subPixOffset[0], -subPixOffset[1]))
		Level.Draw(self)
	
	def SetEditMode(self, mode):
		if mode:
			Prop.Draw = PropDraw
		else:
			if hasattr(Prop, "Draw"):
				Prop.Draw = lambda x: x
	
	###
	###	Level data routines
	###
	
	def GetEntities(self):
		return [(o.__class__.__name__, dict([(s, o.__dict__[s]) for s in ("id", "destination", "rectangle", "description") if s in o.__dict__])) for o in self.layer.GetAll()]
	
	def PackSerial(self):
		return {"level": {"history": self.history, "entities": self.GetEntities(), "startpoints": dict([(s, self.startPoints[s].id) for s in self.startPoints])}}
	
	def UnpackSerial(self, data):
		self.history = data["level"]["history"]
		for s in data['level']['entities']:
			getattr(self, "Create" + s[0], lambda x: x)(s[1])
		sp = data["level"]["startpoints"]
		self.startPoints = dict([(s, self.layer.names[sp[s]]) for s in sp])
	
	def Save(self):
		""" Writes this level to disk """
		out = file(self.basefilename + ".json", "w")
		out.write(dumps(self.PackSerial()))
		out.close()
		self.bitmap.Save(self.basefilename + ".png")
	
	def Load(self):
		""" Reads this level from disk """
		self.UnpackSerial(loads(file(self.basefilename + ".json").read()))
		self.bitmap = Image(self.basefilename + ".png")
		self.AddLayer(self.name, self.layer)
	
	def Layer_backgroundboxes(self, element, size, info, dom):
		""" Legacy SVG level loading code. """
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
	
	def CreatePlatform(self, data):
		self.layer.AddProp(Platform(data["rectangle"], data["id"]))
	
	def CreatePortal(self, data):
		self.layer.AddProp(Portal(data["rectangle"], data["id"], data["destination"]))
	
	def CreateItem(self, data):
		self.layer.AddProp(Item(data["rectangle"], data["id"], data["description"]))
