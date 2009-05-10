from random import randint
from sys import maxint

from PodSix.Resource import *
from PodSix.Concurrent import Concurrent
from PodSix.Rectangle import Rectangle
from PodSix.Config import config
from PodSix.GUI.Button import TextButton

from ColorPicker import ColorPicker

class EditBox(Rectangle, Concurrent):
	def __init__(self, inlist, camera):
		inlist = camera.FromScreenCoordinates(inlist) + [0, 0]
		Rectangle.__init__(self, inlist)
		Concurrent.__init__(self)
		self.camera = camera
		self.color = (255, 255, 255)	
	
	def Draw(self):
		gfx.DrawRect(self.camera.TranslateRectangle(self), self.color, 1)
	
	def SetCorner(self, pos):
		pos = self.camera.FromScreenCoordinates(pos)
		self.Width((pos[0] - self.Left()))
		self.Height((pos[1] - self.Top()))

def editOn(fn):
	def newfn(self, *args, **kwargs):
		if self.mode and self.level:
			return fn(self, *args, **kwargs)
	return newfn

class FamilyButton(TextButton):
	family = []
	def __init__(self, name, parent):
		self.name = name
		self.parent = parent
		self.triggered = False
		TextButton.__init__(self, name, pos = {"right": 0.99, "top": 0.05 + 0.042 * len(self.family)}, colors=[[100, 100, 100], [15, 15, 15]])
		self.family.append(self)
	
	def Draw(self):
		if self.name != '---':
			TextButton.Draw(self)
	
	def Select(self, on=True):
		self.parent.selected = self.name
		self.colors[0] = [100 + 150 * on, 100 + 150 * on, 100 + 150 * on]
	
	def Pressed(self):
		[f.Select(False) for f in self.family]
		self.Select()
		self.triggered = True
		self.parent.CallMethod("Pressed_" + self.name)

class EditButton(TextButton):
	def __init__(self, parent):
		self.parent = parent
		TextButton.__init__(self, "edit", pos = {"right": 0.99, "top": 0.01}, colors=[[100, 100, 100], [15, 15, 15]])
	
	def Pressed(self):
		self.parent.ToggleMode()

class EditLayer(Concurrent, EventMonitor):
	"""
	This layer holds the GUI for editing levels.
	The edit button always shows, but toggling it shows or hides the other stuff.
	"""
	def __init__(self):
		# whether edit mode is showing or not
		self.mode = False
		self.level = None
		self.editButton = EditButton(self)
		Concurrent.__init__(self)
		EventMonitor.__init__(self)
		self.Add(self.editButton)
		for b in ['platform', 'portal', 'item', '---', 'move', 'delete', 'clone', '---', 'draw', 'fill']:
			self.Add(FamilyButton(b, self))
		self.selected = ""
		self.down = False
		self.rect = None
		self.currentSurface = None
		self.color = (255, 255, 255)
		self.colorPicker = ColorPicker(self)
		self.Add(self.colorPicker)
	
	def MakeId(self):
		x = None
		while not x or "prop-%d" % x in self.level.layer.names.keys():
			x = randint(1, maxint)
		return "prop-%d" % x
	
	def SetLevel(self, level):
		self.level = level
		self.level.SetEditLayer(self)
	
	def ToggleMode(self):
		self.mode = not self.mode
		self.editButton.colors[0] = [100 + 150 * self.mode, 100 + 150 * self.mode, 100 + 150 * self.mode]
	
	def On(self):
		return self.mode and self.level
	
	###
	###	Concurrency events
	###
	
	def Pump(self):
		if self.On():
			Concurrent.Pump(self)
			EventMonitor.Pump(self)	
		else:
			self.editButton.Pump()
	
	def Update(self):
		if self.On():
			Concurrent.Update(self)
		else:
			self.editButton.Update()
	
	def Draw(self):
		if self.On():
			Concurrent.Draw(self)
			if self.mode and self.level.camera:
				[o.DrawEdit() for o in self.level.layer.GetAll() if o in self.level.camera.GetVisible()]
		else:
			self.editButton.Draw()
	
	###
	###	Interface events
	###
	
	def GetPropUnderMouse(self, p):
		props = [o for o in self.level.layer.GetAll() if o.TestPoint(p)]
		props.reverse()
		if len(props):
			return props[0]
		else:
			return self.level
	
	@editOn
	def MouseDown(self, e):
		if not len([o for o in self.objects if hasattr(o, 'triggered') and o.triggered]):
			self.down = True
			if self.selected in ['platform', 'portal', 'item']:
				self.rect = EditBox(e.pos, self.level.camera)
				self.Add(self.rect)
			else:
				p = self.level.camera.FromScreenCoordinates(e.pos)	
				if self.selected == 'draw':
					self.currentSurface = self.GetPropUnderMouse(p)
					pos = [int(x * gfx.width) for x in p]
					self.currentSurface.Paint(pos)
				elif self.selected == 'fill':
					pos = [int(x * gfx.width) for x in p]
					self.GetPropUnderMouse(p).Fill(pos)
				elif self.selected == 'move':
					self.currentSurface = self.GetPropUnderMouse(p)
					if self.currentSurface != self.level:
						self.currentSurface.Drag(p)
				elif self.selected == 'clone':
					self.currentSurface = self.GetPropUnderMouse(p)
					if self.currentSurface != self.level:
						self.currentSurface = self.level.Clone(self.currentSurface)
						self.currentSurface.Drag(p)
				elif self.selected == 'delete':
					if self.GetPropUnderMouse(p) != self.level:
						self.level.layer.RemoveProp(self.GetPropUnderMouse(p))
	
	@editOn
	def MouseMove(self, e):
		if self.rect:
			self.rect.SetCorner(e.pos)
		elif self.selected == 'draw' and self.down and self.currentSurface:
			self.currentSurface.Paint([int(x * gfx.width) for x in self.level.camera.FromScreenCoordinates(e.pos)])
		elif self.selected in ('move', 'clone') and self.down and self.currentSurface and self.currentSurface != self.level:
			self.currentSurface.Drag(self.level.camera.FromScreenCoordinates(e.pos))
	
	@editOn
	def MouseUp(self, e):
		self.down = False
		if self.rect and self.rect[2] > 1 and self.rect[3] > 1:
			if self.selected in ['platform', 'portal', 'item']:
				self.rect.Absolute()
				self.level.Create(self.selected, {'rectangle': list(self.rect)})
			self.Remove(self.rect)
			self.rect = None
		if self.currentSurface:
			self.currentSurface.MouseUp()
			self.currentSurface = None

