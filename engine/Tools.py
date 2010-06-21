from math import cos,sin,pi
from os import path
import random

from PodSix.GUI.Button import ImageRadioButton
from PodSix.Resource import *

class DrawTool(ImageRadioButton):
	def __init__(self, parent, buttonGroup, filename="image.png", selected="image-invert.png", iconpos=64, *args, **kwargs):
		self.parent = parent
		ImageRadioButton.__init__(self,
				[Image(path.join("resources", "icons", filename)), Image(path.join("resources", "icons", selected))],
				[gfx.width - 24, iconpos],
				"line", buttonGroup)
		
		self.currentSurface = None
		self.lastPos = None
		self.mouseDown = False
	
	def OnMouseDown(self, pos):
		self.mouseDown = True
		coordinates = self.parent.level.camera.FromScreenCoordinates(pos)
		self.currentSurface = self.parent.GetPropUnderMouse(coordinates)
		pos = [int(x * gfx.width) for x in coordinates]
		self.lastPos = pos
		self.parent.game.net.SendWithID({"action": "edit", "instruction": "pendown", "tool": self.__class__.__name__})
		return pos
	
	def OnMouseMove(self, pos):
		absolute = [int(x * gfx.width) for x in self.parent.level.camera.FromScreenCoordinates(pos)]
		if self.mouseDown:
			self.parent.game.net.SendWithID({"action": "edit", "instruction": "penmove", "tool": self.__class__.__name__})
		oldLastPos = self.lastPos
		self.lastPos = absolute
		return absolute, oldLastPos
	
	def OnMouseUp(self,pos):
		if not self.currentSurface != self:
			self.parent.game.net.SendWithID({"action": "edit", "instruction": "penup", "tool": self.__class__.__name__})
		self.currentSurface = None
		self.lastPos = None
		self.mouseDown = False
	
	def Pressed(self):
		self.parent.selected = self		
		self.parent.CallMethod("Pressed_" + self.name)

class LineTool(DrawTool):
	"""Line drawing tool"""
	
	def __init__(self, parent, buttonGroup, *args, **kwargs):
		DrawTool.__init__(self,parent,buttonGroup,filename="line.png",selected="line-invert.png",iconpos=7 * 33 + 72,*args,**kwargs)
		
		self.mouseDownPosition = None
		self.savedImage = None
				
	def OnMouseDown(self, pos):
		pos = DrawTool.OnMouseDown(self,pos)
		self.savedImage, self.image_start, dummy = self.currentSurface.SubImage(pos,pos)
		self.currentSurface.Paint(pos)
		self.mouseDownPosition = pos
		
	def OnMouseMove(self,pos):
		pos, lastPos = DrawTool.OnMouseMove(self, pos)
		if self.currentSurface and lastPos != pos:
			if self.savedImage:
				# there is an image saved. paste it
				self.currentSurface.PasteSubImage(self.savedImage, self.image_start)
			#save area of image so we can revert it when drawing a new line
			self.savedImage, self.image_start, dummy = self.currentSurface.SubImage(self.mouseDownPosition,pos)
			self.currentSurface.Line(self.mouseDownPosition, pos)
	
	def OnMouseUp(self,pos):
		DrawTool.OnMouseUp(self,pos)
		self.mouseDownPosition = None

class PenTool(DrawTool):
	"""Pen drawing tool"""
	
	def __init__(self, parent, buttonGroup, *args, **kwargs):
		DrawTool.__init__(self,parent,buttonGroup,filename="pen.png",selected="pen-invert.png",iconpos=8 * 33 + 72,*args,**kwargs)	
	
	def OnMouseDown(self, pos):
		p = DrawTool.OnMouseDown(self,pos)
		self.currentSurface.Paint(p)
	
	def OnMouseMove(self,pos):
		pos, lastPos = DrawTool.OnMouseMove(self, pos)
		if self.currentSurface and lastPos != pos:
			self.currentSurface.Line(lastPos, pos)

class FillTool(DrawTool):
	"""Flood fill tool"""
	def __init__(self, parent, buttonGroup, *args, **kwargs):
		DrawTool.__init__(self,parent,buttonGroup,filename="fill.png",selected="fill-invert.png",iconpos=9 * 33 + 72,*args,**kwargs)	
	
	def OnMouseDown(self, pos):
		p = DrawTool.OnMouseDown(self,pos)
		self.currentSurface.Fill(p, self.currentSurface == self.parent.level)

class AirbrushTool(DrawTool):
	"""Old Amiga-style airbrush tool"""
	def __init__(self, parent, buttonGroup, *args, **kwargs):
		DrawTool.__init__(self,parent,buttonGroup,filename="airbrush.png",selected="airbrush-invert.png",iconpos=10 * 33 + 72,*args,**kwargs)	
		self.radius = 3000.0 / gfx.width
		self.position = None		# where the Pump() should draw to
		
	def OnMouseDown(self, pos):
		p = DrawTool.OnMouseDown(self,pos)
		self.PlotRandomPoint(p)	
		self.position = p
	
	def OnMouseMove(self, pos):
		pos, lastPos = DrawTool.OnMouseMove(self, pos)
		if self.currentSurface:
			self.PlotRandomPoint( pos )
			self.position = pos
	
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
	
