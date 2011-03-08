from os import path

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
		self.color = (255, 255, 255)
	
	def OnMouseDown(self, pos):
		coordinates = self.parent.level.camera.FromScreenCoordinates(pos)
		surface = self.parent.GetPropUnderMouse(coordinates)
		absolute = [int(x * gfx.width) for x in coordinates]
		self.parent.RecordEdit({"action": "edit", "instruction": "pendown", "tool": self.__class__.__name__, "pos": absolute, "objectid": surface.id, "color": tuple(self.parent.color)})
		return self.PenDown(absolute, surface, self.parent.color)
	
	def PenDown(self, pos, surface, color):
		self.mouseDown = True
		self.lastPos = pos
		self.currentSurface = surface
		self.color = color
		return pos, self.currentSurface
	
	def NetworkPenDown(self, pos, surface, color):
		self.PenDown(pos, surface, color)
	
	def OnMouseMove(self, pos):
		absolute = [int(x * gfx.width) for x in self.parent.level.camera.FromScreenCoordinates(pos)]
		if self.mouseDown:
			self.parent.RecordEdit({"action": "edit", "instruction": "penmove", "tool": self.__class__.__name__, "pos": absolute})
		return self.PenMove(absolute)
	
	def NetworkPenMove(self, pos):
		self.PenMove(pos)
	
	def PenMove(self, pos):
		oldLastPos = self.lastPos
		self.lastPos = pos
		return pos, oldLastPos
	
	def OnMouseUp(self, pos):
		if not self.currentSurface != self:
			self.parent.RecordEdit({"action": "edit", "instruction": "penup", "tool": self.__class__.__name__})
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
	help_text = "draw line"
	def __init__(self, parent, buttonGroup=None, *args, **kwargs):
		DrawTool.__init__(self,parent,buttonGroup,filename="line.png",selected="line-invert.png",iconpos=7 * 33 + 72,*args,**kwargs)
		
		self.mouseDownPosition = None
		self.savedImage = None
	
	def PenDown(self, pos, surface, color):
		pos, surface = DrawTool.PenDown(self, pos, surface, color)
		self.savedImage, self.image_start, dummy = self.currentSurface.SubImage(pos, pos)
		self.currentSurface.Paint(pos, color)
		self.mouseDownPosition = pos
	
	def PenMove(self, pos):
		pos, lastPos = DrawTool.PenMove(self, pos)
		if self.currentSurface and lastPos != pos:
			if self.savedImage:
				# there is an image saved. paste it
				self.currentSurface.PasteSubImage(self.savedImage, self.image_start)
			#save area of image so we can revert it when drawing a new line
			self.savedImage, self.image_start, dummy = self.currentSurface.SubImage(self.mouseDownPosition,pos)
			self.currentSurface.Line(self.mouseDownPosition, pos, self.color)
		return pos, lastPos
	
	def PenUp(self):
		DrawTool.PenUp(self)
		self.mouseDownPosition = None

class PenTool(DrawTool):
	"""Pen drawing tool"""
	help_text = "draw"	
	def __init__(self, parent, buttonGroup=None, *args, **kwargs):
		DrawTool.__init__(self,parent,buttonGroup,filename="pen.png",selected="pen-invert.png",iconpos=8 * 33 + 72,*args,**kwargs)	
	
	def PenDown(self, pos, surface, color):
		pos, surface = DrawTool.PenDown(self, pos, surface, color)
		self.currentSurface.Paint(pos, color)
	
	def PenMove(self, pos):
		pos, lastPos = DrawTool.PenMove(self, pos)
		if self.currentSurface and lastPos != pos:
			self.currentSurface.Line(lastPos, pos, self.color)
		return pos, lastPos

class FillTool(DrawTool):
	"""Flood fill tool"""
	help_text = "fill"
	def __init__(self, parent, buttonGroup=None, *args, **kwargs):
		DrawTool.__init__(self,parent,buttonGroup,filename="fill.png",selected="fill-invert.png",iconpos=9 * 33 + 72,*args,**kwargs)	
	
	def PenDown(self, pos, surface, color):
		pos, surface = DrawTool.PenDown(self, pos, surface, color)
		self.currentSurface.Fill(pos, color, self.currentSurface == self.parent.level)

class AirbrushTool(DrawTool):
	"""Old Amiga-style airbrush tool"""
	help_text = "airbrush"
	def __init__(self, parent, buttonGroup=None, *args, **kwargs):
		DrawTool.__init__(self,parent,buttonGroup,filename="airbrush.png",selected="airbrush-invert.png",iconpos=10 * 33 + 72,*args,**kwargs)	
		self.radius = 3000.0 / gfx.width
		self.position = None		# where the Pump() should draw to
	
	def PenDown(self, pos, surface, color):
		pos, surface = DrawTool.PenDown(self, pos, surface, color)
		x,y = surface.PlotRandomPoint(pos, self.radius, color)
		self.position = pos
	
	def NetworkPenDown(self, pos, surface, color):
		DrawTool.PenDown(self, pos, surface, color)
	
	def NetworkPenMove(self, pos):
		DrawTool.PenMove(self, pos)
	
	def NetworkPenUp(self):
		DrawTool.PenUp(self)
	
	def NetworkPenData(self, data):
		""" We want to draw a special pixel point. """
		self.currentSurface.Paint(data['pos'], data['color'])
	
	def PenMove(self, pos):
		pos, lastPos = DrawTool.PenMove(self, pos)
		if self.currentSurface:
			xpos, ypos = self.currentSurface.PlotRandomPoint(pos, self.radius, self.color)
			# make sure the paint happens remotely too
			self.parent.RecordEdit({"action": "edit", "instruction": "pendata", "tool": "AirbrushTool", "pos": [xpos, ypos], "objectid": self.currentSurface.id, "color": tuple(self.color)})
			self.position = pos
		return pos, lastPos
	
	def Pump(self):
		"""call me repeatedly to keep the pixels flowing"""
		if self.currentSurface:
			self.currentSurface.PlotRandomPoint(self.position, self.radius, self.color)
		ImageRadioButton.Pump(self)

