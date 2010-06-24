from math import cos,sin,pi
from os import path
import random

from PodSix.GUI.Button import ImageRadioButton
from PodSix.Resource import *

class DrawTool(ImageRadioButton):
	def __init__(self, parent, buttonGroup=None, filename="image.png", selected="image-invert.png", iconpos=64, *args, **kwargs):
		self.parent = parent
		if buttonGroup:
			ImageRadioButton.__init__(self,
				[Image(path.join("resources", "icons", filename)), Image(path.join("resources", "icons", selected))],
				[gfx.width - 24, iconpos],
				"line", buttonGroup)
		
		self.currentSurface = None
		self.lastPos = None
		self.mouseDown = False
	
	def OnMouseDown(self, pos):
		coordinates = self.parent.level.camera.FromScreenCoordinates(pos)
		surface = self.parent.GetPropUnderMouse(coordinates)
		absolute = [int(x * gfx.width) for x in coordinates]
		self.parent.game.net.SendWithID({"action": "edit", "instruction": "pendown", "tool": self.__class__.__name__, "pos": absolute, "objectid": surface.id})
		return self.PenDown(absolute, surface)
	
	def PenDown(self, pos, surface):
		self.mouseDown = True
		self.lastPos = pos
		self.currentSurface = surface
		return pos, self.currentSurface
	
	def NetworkPenDown(self, pos, surface):
		self.PenDown(pos, surface)
	
	def OnMouseMove(self, pos):
		absolute = [int(x * gfx.width) for x in self.parent.level.camera.FromScreenCoordinates(pos)]
		if self.mouseDown:
			self.parent.game.net.SendWithID({"action": "edit", "instruction": "penmove", "tool": self.__class__.__name__, "pos": absolute})
		return self.PenMove(absolute)
	
	def NetworkPenMove(self, pos):
		self.PenMove(pos)
	
	def PenMove(self, pos):
		oldLastPos = self.lastPos
		self.lastPos = pos
		return pos, oldLastPos
	
	def OnMouseUp(self, pos):
		if not self.currentSurface != self:
			self.parent.game.net.SendWithID({"action": "edit", "instruction": "penup", "tool": self.__class__.__name__})
		return self.PenUp()
	
	def NetworkPenUp(self):
		self.PenUp()
	
	def PenUp(self):
		self.currentSurface = None
		self.lastPos = None
		self.mouseDown = False
	
	def Pressed(self):
		self.parent.selected = self		
		self.parent.CallMethod("Pressed_" + self.name)

class LineTool(DrawTool):
	"""Line drawing tool"""
	def __init__(self, parent, buttonGroup=None, *args, **kwargs):
		DrawTool.__init__(self,parent,buttonGroup,filename="line.png",selected="line-invert.png",iconpos=7 * 33 + 72,*args,**kwargs)
		
		self.mouseDownPosition = None
		self.savedImage = None
	
	def PenDown(self, pos, surface):
		pos, surface = DrawTool.PenDown(self, pos, surface)
		self.savedImage, self.image_start, dummy = self.currentSurface.SubImage(pos, pos)
		self.currentSurface.Paint(pos)
		self.mouseDownPosition = pos
	
	def PenMove(self, pos):
		pos, lastPos = DrawTool.PenMove(self, pos)
		if self.currentSurface and lastPos != pos:
			if self.savedImage:
				# there is an image saved. paste it
				self.currentSurface.PasteSubImage(self.savedImage, self.image_start)
			#save area of image so we can revert it when drawing a new line
			self.savedImage, self.image_start, dummy = self.currentSurface.SubImage(self.mouseDownPosition,pos)
			self.currentSurface.Line(self.mouseDownPosition, pos)
		return pos, lastPos
	
	def PenUp(self):
		DrawTool.PenUp(self)
		self.mouseDownPosition = None

class PenTool(DrawTool):
	"""Pen drawing tool"""
	
	def __init__(self, parent, buttonGroup=None, *args, **kwargs):
		DrawTool.__init__(self,parent,buttonGroup,filename="pen.png",selected="pen-invert.png",iconpos=8 * 33 + 72,*args,**kwargs)	
	
	def PenDown(self, pos, surface):
		pos, surface = DrawTool.PenDown(self, pos, surface)
		self.currentSurface.Paint(pos)
	
	def PenMove(self,pos):
		pos, lastPos = DrawTool.PenMove(self, pos)
		if self.currentSurface and lastPos != pos:
			self.currentSurface.Line(lastPos, pos)
		return pos, lastPos

class FillTool(DrawTool):
	"""Flood fill tool"""
	def __init__(self, parent, buttonGroup=None, *args, **kwargs):
		DrawTool.__init__(self,parent,buttonGroup,filename="fill.png",selected="fill-invert.png",iconpos=9 * 33 + 72,*args,**kwargs)	
	
	def PenDown(self, pos, surface):
		pos, surface = DrawTool.PenDown(self, pos, surface)
		self.currentSurface.Fill(pos, self.currentSurface == self.parent.level)

class AirbrushTool(DrawTool):
	"""Old Amiga-style airbrush tool"""
	def __init__(self, parent, buttonGroup=None, *args, **kwargs):
		DrawTool.__init__(self,parent,buttonGroup,filename="airbrush.png",selected="airbrush-invert.png",iconpos=10 * 33 + 72,*args,**kwargs)	
		self.radius = 3000.0 / gfx.width
		self.position = None		# where the Pump() should draw to
	
	def PenDown(self, pos, surface):
		pos, surface = DrawTool.PenDown(self, pos, surface)
		x,y = self.PlotRandomPoint(pos)
		self.position = pos
	
	def NetworkPenDown(self, pos, surface):
		DrawTool.PenDown(self, pos, surface)
	
	def NetworkPenMove(self, pos):
		DrawTool.PenMove(self, pos)
	
	def NetworkPenUp(self):
		DrawTool.PenUp(self)
	
	def NetworkPenData(self, data):
		""" We want to draw a special pixel point. """
		self.currentSurface.Paint(data['pos'])
	
	def PenMove(self, pos):
		pos, lastPos = DrawTool.PenMove(self, pos)
		if self.currentSurface:
			self.PlotRandomPoint( pos )
			self.position = pos
		return pos, lastPos
	
	def Pump(self):
		"""call me repeatedly to keep the pixels flowing"""
		if self.currentSurface:
			self.PlotRandomPoint(self.position)
		ImageRadioButton.Pump(self)
	
	def PlotRandomPoint(self, pos):
		"""Plot a random point on the currentSurface a distance 'radius' away from pos"""
		pix = color = self.parent.color
		count = 10
		while pix == color and count > 0:
			theta = random.random() * 2.0 * pi
			r = self.radius * random.random()
			xpos = int(r * cos(theta) + pos[0])
			ypos = int(r * sin(theta) + pos[1])
			try:
				pix = self.currentSurface.GetPixel([xpos, ypos])
			except IndexError, ie:
				pass
			count -= 1
		self.currentSurface.Paint([xpos, ypos])
		# make sure the paint happens remotely too
		self.parent.game.net.SendWithID({"action": "edit", "instruction": "pendata", "tool": "AirbrushTool", "pos": [xpos, ypos], "objectid": self.currentSurface.id})
		return xpos, ypos
