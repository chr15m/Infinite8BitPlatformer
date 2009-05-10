from os import path, rmdir, unlink, makedirs
import tempfile
import zipfile
from cStringIO import StringIO

from simplejson import dumps, loads

from PodSix.Platformer.Level import Level
from PodSix.Platformer.Layer import Layer

from PodSix.SVGLoader import SVGLoader
from PodSix.Resource import *
from PodSix.Config import config

from BitProps.BitProp import BitProp
from BitProps.BitPlatform import BitPlatform
from BitProps.BitItem import BitItem
from BitProps.BitPortal import BitPortal

from Paintable import Paintable
from BitImage import BitImage

import palettes

if not hasattr(zipfile.ZipFile, "extract"):
	def extract(self, name, dest):
		destdir = path.join(dest, name)
		destdir = destdir[:-len(path.basename(destdir))]
		if not path.exists(destdir):
			makedirs(destdir)
		data = self.read(name)
		out = file(path.join(dest, name), "wb")
		out.write(data)
		out.close()
	zipfile.ZipFile.extract = extract	

class BitLevel(Level, SVGLoader, Paintable):
	def __init__(self, name, editLayer):
		Paintable.__init__(self, editLayer)
		Level.__init__(self, name)
		self.basefilename = path.join("resources", "levels", self.name)
		self.layer = Layer(self)
		self.gravity = self.gravity / config.zoom
		self.palette = "NES"
		self.bitmap = BitImage(size=(1024, 768), depth=8)
		self.history = []
	
	def ApplyPalette(self):
		palette = palettes.all[self.palette]
		self.bitmap.Palette(palette)
		[o.bitmap.Palette(palette) for o in self.layer.GetAll()]
	
	###
	###	UI/Bitmap routines
	###
	
	def Draw(self):
		subPixOffset = self.camera.PixelOffset()
		pixelBoxSize = self.camera.ToPixels().Grow(1, 1)
		box = pixelBoxSize.Clip([0, 0, 1024, 768])
		newbitmap = self.bitmap.SubImage(box).Scale((box.Width() * config.zoom, box.Height() * config.zoom))
		gfx.BlitImage(newbitmap, position=(-subPixOffset[0], -subPixOffset[1]))
		Level.Draw(self)
	
	###
	###	Level data routines
	###
	
	def GetEntities(self):
		return [(o.type, dict([(s, o.__dict__[s]) for s in ("id", "destination", "rectangle", "description") if s in o.__dict__])) for o in self.layer.GetAll()]
	
	def PackSerial(self):
		return {"level": {"history": self.history, "entities": self.GetEntities(), "palette": self.palette, "startpoints": dict([(s, self.startPoints[s].id) for s in self.startPoints])}}
	
	def UnpackSerial(self, data):
		self.history = data["level"]["history"]
		self.palette = data["level"].get("palette", "NES")
		for s in data['level']['entities']:
			self.Create(s[0], s[1])
		sp = data["level"]["startpoints"]
		self.startPoints = dict([(s, self.layer.names[sp[s]]) for s in sp])
	
	def ToString(self):
		""" Turns this level into a zipfile blob """
		data = StringIO()
		zip = zipfile.ZipFile(data, "w")
		tmpfile = tempfile.mkstemp(suffix=".png")[1]
		zip.writestr(path.join(self.name, "level.json"), dumps(self.PackSerial()))
		self.bitmap.surface.convert(16)
		self.bitmap.Save(tmpfile)
		zip.write(tmpfile, path.join(self.name, "level.png"))
		for e in self.layer.GetAll():
			if e.bitmap:
				e.bitmap.surface.convert(16)
				e.bitmap.Save(tmpfile)
				zip.write(tmpfile, path.join(self.name, e.id + ".png"))
		zip.close()
		return data.getvalue()
	
	def Save(self):
		out = file(self.basefilename + ".level.zip", "w")
		out.write(self.ToString())
		out.close()
	
	def Load(self):
		self.FromString(file(self.basefilename + ".level.zip", "r").read())
	
	def FromString(self, data):
		zip = zipfile.ZipFile(StringIO(data), "r")
		self.UnpackSerial(loads(zip.read(path.join(self.name, "level.json"))))
		tmpdir = tempfile.mkdtemp()
		zip.extract(path.join(self.name, "level.png"), tmpdir)
		imgfile = path.join(tmpdir, self.name, "level.png")
		self.bitmap = BitImage(imgfile)
		# remove created temp files
		unlink(imgfile)
		for t, e in self.GetEntities():
			baseimgfile = path.join(self.name, e['id'] + ".png")
			if baseimgfile in zip.namelist():
				zip.extract(baseimgfile, tmpdir)
				imgfile = path.join(tmpdir, baseimgfile)
				self.layer.names[e['id']].bitmap = BitImage(imgfile)
				unlink(imgfile)
		rmdir(imgfile[:-len(path.basename(imgfile))])
		rmdir(tmpdir)
		# set the palette on everything
		self.ApplyPalette()
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
	
	def AddProp(self, prop):
		self.layer.AddProp(prop)
		prop.SetEditLayer(self.editLayer)
		return prop
	
	def Clone(self, which):
		new = self.Create(which.type, {"rectangle": list(which.rectangle)})
		new.bitmap = BitImage(image=which.bitmap)
		return new
	
	def Create(self, which, data):
		newthing = getattr(self, "Create" + which[0].capitalize() + which[1:], lambda x: x)(data)
		newthing.bitmap.Palette(palettes.all[self.palette])
	
	def CreatePlatform(self, data):
		return self.AddProp(BitPlatform(data["rectangle"], data.get("id", None), editLayer=self.editLayer))
	
	def CreatePortal(self, data):
		return self.AddProp(BitPortal(data["rectangle"], data.get("id", None), data.get("destination", ""), editLayer=self.editLayer))
	
	def CreateItem(self, data):
		return self.AddProp(BitItem(data["rectangle"], data.get("id", None), data.get("description", ""), editLayer=self.editLayer))

