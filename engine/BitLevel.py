from os import path, rmdir, unlink, makedirs
from sys import platform, argv
import tempfile
import zipfile
from cStringIO import StringIO

try:
	from json import dumps, loads
except ImportError:
	from simplejson import dumps, loads

from PodSix.Platformer.Level import Level
from PodSix.Platformer.Layer import Layer

from PodSix.SVGLoader import SVGLoader
from PodSix.Resource import *
from PodSix.Config import config
from PodSix.Rectangle import Rectangle

from BitProps.BitProp import BitProp
from BitProps.BitPlatform import BitPlatform
from BitProps.BitLadder import BitLadder
from BitProps.BitItem import BitItem
from BitProps.BitPortal import BitPortal

from Paintable import Paintable
from BitImage import BitImage

import palettes

from pygame import Surface

# this is a horrible Windows 7 hack apparently
## Patrick: continue even if there are errors cleaning up temp
import time
_unlink = unlink
def unlink(*args):
	sleep = 0.002
	for attempt in range(5):
		try:
			_unlink(*args)
			return
		except:
			time.sleep(sleep)
			sleep *= 2

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
		# self.name should be self.id
		self.id = name
		self.basefilename = path.join("resources", "levels", self.name)
		self.layer = Layer(self)
		self.gravity = self.gravity / config.zoom
		self.palette = "NES"
		self.size = (1024, 768)
		self.sizerect = (0, 0) + self.size
		self.bitmap = BitImage(size=self.size)
		self.bitmap.Fill((255, 0, 255))
		self.history = []
		self.startPoints = {}
		self.displayName = name
		self.bgColor = (150, 150, 150)
		self.scaledbitmap = None
		self.lastLocalEdit = None
		self.lastRemoteEdit = None
		self.lastAppliedEdit = None
		self.loaded = False
	
	#def ApplyPalette(self):
		#palette = palettes.all[self.palette]
		#self.bitmap.Palette(palette)
		#[o.bitmap.Palette(palette) for o in self.layer.GetAll()]
	
	###
	###	UI/Bitmap routines
	###
	
	def Draw(self):
		gfx.SetBackgroundColor(self.bgColor)
		subPixOffset = self.camera.PixelOffset()
		pixelBoxSize = self.camera.ToPixels().Grow(1, 1)
		box = pixelBoxSize.Clip(self.sizerect)
		if box.Width() > 0 and box.Height() > 0:
			self.scaledbitmap = self.bitmap.SubImage(box).Scale((box.Width() * config.zoom, box.Height() * config.zoom), self.scaledbitmap)
			gfx.BlitImage(self.scaledbitmap, position=(-subPixOffset[0], -subPixOffset[1]))
		Level.Draw(self)
		
	def SubImage(self, corner1, corner2):
		"""given two opposite corners of a box, return an image representing the subimage in that box"""
		# turn corners into topleft and bottomright
		topleft = [corner1[x] if corner1[x]<corner2[x] else corner2[x] for x in [0,1]]
		bottomright = [corner1[x] if corner1[x]>corner2[x] else corner2[x] for x in [0,1]]
		widthheight = [B-A+1 for A,B in zip(topleft,bottomright)]
		
		box = Rectangle(topleft+widthheight)
		sub = self.bitmap.SubImage(box,copy=True)		#.Scale((box.Width() * config.zoom, box.Height() * config.zoom), self.scaledbitmap)
		
		# this sub contains alpha. So lets fill those areas with the background colour
		#sub.RemoveAlpha(self.bgColor)
		sub.RemoveAlpha()
				
		return sub, topleft, bottomright
		
	def PasteSubImage(self, image, pos):
		self.bitmap.Blit(image, pos)

	
	###
	###	Level data routines
	###
	
	def GetEntities(self):
		return [(o.type, dict([(s, o.__dict__[s]) for s in ("id", "destination", "rectangle", "description") if s in o.__dict__])) for o in self.layer.GetAll()]
	
	def PropFromId(self, objectid):
		objs = [o for o in self.layer.GetAll()+[self] if o.id == objectid]
		return len(objs) and objs[0] or None
	
	def PackSerial(self):
		return {"level": {"name": self.displayName, "history": self.history, "entities": self.GetEntities(), "palette": self.palette, "background": self.bgColor, "startpoints": dict([(s, self.startPoints[s].id) for s in self.startPoints])}}
	
	def UnpackSerial(self, data):
		self.displayName = data["level"].get("name", "level" + self.name)
		self.history = data["level"]["history"]
		self.palette = data["level"].get("palette", "NES")
		for s in data['level']['entities']:
			self.Create(s[0], s[1])
		self.bgColor = tuple(data["level"].get("background", (150, 150, 150)))
		sp = data["level"]["startpoints"]
		self.startPoints = dict([(s, self.layer.names[sp[s]]) for s in sp])
	
	def ToString(self):
		""" Turns this level into a zipfile blob """
		data = StringIO()
		zip = zipfile.ZipFile(data, "w")
		tmpfile = tempfile.mkstemp(suffix=".png")[1]
		zip.writestr(self.name + "/level.json", dumps(self.PackSerial()))
		self.bitmap.Save(tmpfile)
		zip.write(tmpfile, self.name + "/level.png")
		for e in self.layer.GetAll():
			if e.bitmap:
				e.bitmap.Save(tmpfile)
				zip.write(tmpfile, (self.name + "/" + e.id + ".png").encode('ascii'))
		zip.close()
		return data.getvalue()
	
	def Save(self):
		mode = "wb"
		out = file(self.basefilename + ".level.zip", mode)
		out.write(self.ToString())
		out.close()
	
	def Load(self):
		self.FromString(file(self.basefilename + ".level.zip", "rb").read())
		# find the correct indicies for local and remote applied
		for h in self.history:
			isRemoteEdit = h.has_key("servertime")
			if isRemoteEdit:
				if not self.lastRemoteEdit:
					self.lastRemoteEdit = h
				elif self.history.index(h) > self.history.index(self.lastRemoteEdit):
					self.lastRemoteEdit = h
			else:
				if not self.lastLocalEdit:
					self.lastLocalEdit = h
				elif self.history.index(h) > self.history.index(self.lastLocalEdit):
					self.lastLocalEdit = h
			# NOTE: this might be incorrect, might have to actually figure out what the last applied remote was
			self.lastAppliedEdit = self.lastRemoteEdit
		self.loaded = True
	
	def Initialise(self):
		""" Initialise a completely blank new level. """
		#self.ApplyPalette()
		self.AddLayer(self.name, self.layer)
	
	def FromString(self, data):
		zip = zipfile.ZipFile(StringIO(data), "r")
		self.UnpackSerial(loads(zip.read(self.name + "/level.json")))
		imgfile = StringIO(zip.read(self.name + "/level.png"))
		self.bitmap = BitImage(imgfile)
		for t, e in self.GetEntities():
			baseimgfile = self.name + "/" + e['id'] + ".png"
			if baseimgfile in zip.namelist():
				imgfile = StringIO(zip.read(baseimgfile))
				self.layer.names[e['id']].bitmap = BitImage(imgfile)
		# set the palette on everything
		#self.ApplyPalette()
		self.AddLayer(self.name, self.layer)
	
	def AddRemoteLevelHistory(self, historyitem, publicID, playerID):
		"""
			Records a single item of level edit history.
			Stuff always comes from the server in the correct order, but:
			Local stuff may happen before it's supposed to.
			This should ensure those premature local items get re-applied when neccessary.
		"""
		# cleaneditem used to check if we already have this edit in the history
		cleaneditem = historyitem.copy()
		# remove the network specific fields to make a clean comparison
		del cleaneditem['editid']
		del cleaneditem['level']
		del cleaneditem['servertime']
		if publicID == cleaneditem['id']:
			cleaneditem['id'] = playerID
		
		# assume we did not find the edit
		pos = None
		
		try:
			# is the item an unaccounted for previous-local edit
			pos = self.history.index(cleaneditem)
		except ValueError:
			pass
		
		#print "POINTERS:", pos
		#print "lastLocalEdit", self.lastLocalEdit and self.history.index(self.lastLocalEdit)
		#print "lastAppliedEdit", self.lastAppliedEdit and self.history.index(self.lastAppliedEdit)
		#print "lastRemoteEdit", self.lastRemoteEdit and self.history.index(self.lastRemoteEdit)
		
		if pos is None:
			# item is not in the history as one of our own edits
			# check if item is already in our history 
			if historyitem in self.history:
				# should this happen? probably never right?
				#if "debug" in argv:
				#	print "history item ignored - already in history: ", historyitem
				#	pprint(self.history[-10:])
				return None
			else:
				self.history.append(historyitem)
				self.lastAppliedEdit = self.history[-1]
				self.lastRemoteEdit = self.history[-1]
				#if "debug" in argv:
				#	print 'unseen remote edit, applying', cleaneditem
				#	pprint(self.history[-10:])
				return True
		else:
			# if we get here, the cleaneditem was in our history
			# this means it was a local edit that we haven't yet received from the server
			if self.lastLocalEdit and pos == self.history.index(self.lastLocalEdit) and self.lastAppliedEdit and self.history.index(self.lastAppliedEdit) > self.history.index(self.lastLocalEdit):
				# we got here because it was a local edit, but there has been a more recent remote edit
				# so we move it to the top of the history stack (the remote history happened before)
				# hmmm, couldn't this be better accomplished by checking servertimes?
				del self.history[pos]
				self.lastLocalEdit = None
				self.history.append(historyitem)
				self.lastAppliedEdit = self.history[-1]
				self.lastRemoteEdit = self.history[-1]
				#if "debug" in argv:
				#	print "Remote edit matches local edit but there have been more recent remote edits - moved from %d to the top of the stack: " % pos, historyitem
				#	pprint(self.history[-10:])
				return True
			else:
				# replace our own edit with the network version
				self.history[pos] = historyitem
				self.lastRemoteEdit = self.history[pos]
				#if "debug" in argv:
				#	print "Replaced local edit history with remote at position %d with %s" % (pos, str(historyitem))
				#	pprint(self.history[-10:])
	
	def AddLocalLevelHistory(self, historyitem):
		# this is just a local edit, so just record and apply it no matter what
		self.history.append(historyitem)
		self.lastLocalEdit = self.history[-1]
		#if "debug" in argv:
		#	print 'applying local edit', self.history.index(historyitem), historyitem
		#	#pprint(self.history[-10:])
		return True
	
	def LastEdit(self):
		return self.lastRemoteEdit and self.lastRemoteEdit['editid'] or 0
	
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
	
	def SetName(self, name):
		self.displayName = name
	
	def AddProp(self, prop):
		self.layer.AddProp(prop)
		prop.SetEditLayer(self.editLayer)
		return prop
	
	def Clone(self, which, newid=None):
		new = self.Create(which.type, {"rectangle": list(which.rectangle), "id": newid})
		new.bitmap = BitImage(image=which.bitmap)
		return new
	
	def Create(self, which, data):
		newthing = getattr(self, "Create" + which.capitalize(), lambda x: x)(data)
		#newthing.bitmap.Palette(palettes.all[self.palette])
		return newthing
	
	def CreatePlatform(self, data):
		return self.AddProp(BitPlatform(data["rectangle"], data.get("id", None), editLayer=self.editLayer))

	def CreateLadder(self, data):
		return self.AddProp(BitLadder(data["rectangle"], data.get("id", None), editLayer=self.editLayer))
	
	def CreatePortal(self, data):
		return self.AddProp(BitPortal(data["rectangle"], data.get("id", None), data.get("destination", ""), editLayer=self.editLayer))
	
	def CreateItem(self, data):
		return self.AddProp(BitItem(data["rectangle"], data.get("id", None), data.get("description", ""), editLayer=self.editLayer))

