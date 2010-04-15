from random import randint
from sys import maxint
from os import path

from PodSix.Resource import *
from PodSix.Concurrent import Concurrent
from PodSix.Rectangle import Rectangle
from PodSix.Config import config
from PodSix.GUI.Button import TextButton, ImageButton, ImageRadioButton, ImageRadioButtonGroup
from PodSix.Platformer.Item import Item
from PodSix.Platformer.Platform import Platform

from ColorPicker import ColorPicker
from BitLevel import BitLevel

from Tools import PenTool, LineTool, FillTool, AirbrushTool

class EditBox(Rectangle, Concurrent):
	def __init__(self, inlist, camera):
		inlist = camera.FromScreenCoordinates(inlist) + [0, 0]
		Rectangle.__init__(self, inlist)
		Concurrent.__init__(self)
		self.camera = camera
		self.color = (255, 255, 255)	
	
	def Draw(self):
		gfx.DrawRect(self.camera.TranslateRectangle(self), self.color, 1)
	
	def SetCorner(self, pos, bounds=None):
		pos = self.camera.FromScreenCoordinates(pos)
		if bounds:
			self.Width(max(-bounds[0], min(pos[0] - self.Left(), bounds[0])))
			self.Height(max(-bounds[1], min(pos[1] - self.Top(), bounds[1])))
		else:
			self.Width((pos[0] - self.Left()))
			self.Height((pos[1] - self.Top()))

def editOn(fn):
	def newfn(self, *args, **kwargs):
		if self.mode and self.level:
			return fn(self, *args, **kwargs)
	return newfn

class PortalDestinationIcon(ImageButton):
	def __init__(self, parent):
		self.parent = parent
		ImageButton.__init__(self, [Image(path.join("resources", "icons", "portal.png")), Image(path.join("resources", "icons", "portal-invert.png"))], [60, 24])
		self.destination = None 
	
	def Pressed(self):
		# cancel the currently rememebered portal
		self.destination = None
	
	def Draw(self):
		if self.destination:
			ImageButton.Draw(self)

class FamilyButton(ImageRadioButton):
	btncount = 0
	def __init__(self, name, parent, buttonGroup):
		self.parent = parent
		if name != "---":
			ImageRadioButton.__init__(self,
				[Image(path.join("resources", "icons", name + ".png")), Image(path.join("resources", "icons", name + "-invert.png"))],
				[gfx.width - 24, self.__class__.btncount * 36 + 64],
				name, buttonGroup)
			self.__class__.btncount += 1
		else:
			self.__class__.btncount += 0.5
	
	def Draw(self):
		if self.name != '---':
			ImageButton.Draw(self)
	
	def Pressed(self):
		self.parent.selected = self.name
		self.parent.CallMethod("Pressed_" + self.name)

class SaveButton(ImageButton):
	def __init__(self, parent):
		self.parent = parent
		ImageButton.__init__(self, [Image(path.join("resources", "icons", "save.png")), Image(path.join("resources", "icons", "save-invert.png"))], [gfx.width - 60, 24])
	
	def Pressed(self):
		self.parent.SaveLevel()


class NewButton(ImageButton):
	def __init__(self, parent):
		self.parent = parent
		ImageButton.__init__(self, [Image(path.join("resources","icons", "new.png")), Image(path.join("resources", "icons", "new-invert.png"))], [gfx.width - 94, 24])
	
	def Pressed(self):
		self.parent.NewLevel()

class EditButton(ImageButton):
	def __init__(self, parent):
		self.parent = parent
		ImageButton.__init__(self, [Image(path.join("resources", "icons", "edit.png")), Image(path.join("resources", "icons", "edit-invert.png"))], [gfx.width - 24, 24], toggle=True)
	
	def Pressed(self):
		self.parent.ToggleMode()

class EditInterface(Concurrent):
	pass

class EditLayer(Concurrent, EventMonitor):
	"""
	This layer holds the GUI for editing levels.
	The edit button always shows, but toggling it shows or hides the other stuff.
	"""
	def __init__(self, levelmanager):
		# whether edit mode is showing or not
		self.levelmanager = levelmanager
		self.mode = False
		self.level = None
		self.editButton = EditButton(self)
		Concurrent.__init__(self)
		EventMonitor.__init__(self)
		# make sure we are placed in front of other things
		self.priority = 2
		# edit button turns on the other buttons
		self.Add(self.editButton)
		# all the other buttons
		self.buttonGroup = ImageRadioButtonGroup()
		# hold on to all the buttons
		self.editInterface = EditInterface()
		self.editInterface.Add(self.buttonGroup)
		for b in ['platform', 'portal', 'item', '---', 'move', 'delete', 'clone']:
			FamilyButton(b, self, self.buttonGroup)
		
		self.pentool = PenTool(self, self.buttonGroup)
		self.linetool = LineTool(self, self.buttonGroup)
		self.filltool = FillTool(self, self.buttonGroup)
		self.airbrushtool = AirbrushTool(self, self.buttonGroup)
		
		# the save button
		self.editInterface.Add(SaveButton(self))
		self.editInterface.Add(NewButton(self))
		# portal destination selector
		self.portalDestinationIcon = PortalDestinationIcon(self)
		self.editInterface.Add(self.portalDestinationIcon)
		# other stuff
		self.selected = ""
		self.down = False
		self.rect = None
		self.currentSurface = None
		self.color = (255, 255, 255)
		self.colorPicker = ColorPicker(self)
		self.editInterface.Add(self.colorPicker)
		self.lastHover = None
		
		# for some tools we need to know where the mouse button down event happened, so we can rubber band and the like...
		self.mouseDownPosition = [None,None]
		
		# for some tools, while the mouse is moving, we need to know the last mousemove pixel position. This stores that.
		# this way we can tell wether a mouse move actually moves through a large pixel to another
		self.mouseMovePosition = [None,None]
		
		# saved subimage for rubber banding
		self.savedImage = None
		
		# for line tool
		self.image_start = None
	
	def MakeId(self):
		x = None
		while not x or "prop-%d" % x in self.level.layer.names.keys():
			x = randint(1, maxint)
		return "prop-%d" % x
	
	def SetLevel(self, level):
		""" Called by LevelManager. """
		self.level = level
		self.level.SetEditLayer(self)
	
	def SetPortalDestination(self, destination):
		self.portalDestinationIcon.destination = destination
	
	def GetPortalDestination(self):
		return self.portalDestinationIcon.destination
	
	def UpdateItemDescription(self, description):
		self.lastHover.description = description
		self.levelmanager.hud.chatBox.RevertText()
	
	def ToggleMode(self):
		self.mode = self.editButton.down
	
	def SaveLevel(self):
		self.levelmanager.SaveLevel()
	
	def NewLevel(self):
		newlevel = self.levelmanager.NewLevel()
		newlevel.Initialise()
		dest = newlevel.Create("platform", {'rectangle': [0.48, 0.495, 0.04, 0.01]})
		player = self.levelmanager.player
		srcportal = self.level.Create("portal", {'destination': "level" + newlevel.name + ":" + dest.id, 'rectangle': [player.rectangle.CenterX() - 0.01, player.GetBottom() - 0.03, 0.02, 0.03]})
		destportal = newlevel.Create("portal", {'destination': "level" + self.level.name + ":" + srcportal.id, 'rectangle': [0.49, 0.465, 0.02, 0.03]})
		srcportal.destination = "level" + newlevel.name + ":" + destportal.id
		#sfx.PlaySound("portal")
		#self.levelmanager.SetLevel("level" + newlevel.name, dest.id)
	
	def On(self):
		return self.mode and self.level
	
	###
	###	Concurrency events
	###
	
	def Pump(self):
		if self.On():
			self.editInterface.Pump()
			Concurrent.Pump(self)
			EventMonitor.Pump(self)
		else:
			self.editButton.Pump()
	
	def Update(self):
		if self.On():
			self.editInterface.Update()
			Concurrent.Update(self)
		else:
			self.editButton.Update()
	
	def Draw(self):
		if self.On():
			Concurrent.Draw(self)
			if self.mode and self.level.camera:
				[o.DrawEdit() for o in self.level.layer.GetAll() if o in self.level.camera.GetVisible()]
			self.editInterface.Draw()
			self.editButton.Draw()
		
			self.pentool.Draw()
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
		if not len([o for o in self.editInterface.objects + self.objects if hasattr(o, 'triggered') and o.triggered]):
			self.down = True
			if self.selected in ['platform', 'portal', 'item']:
				self.rect = EditBox(e.pos, self.level.camera)
				self.Add(self.rect)
			else:
				p = self.level.camera.FromScreenCoordinates(e.pos)	
				if self.selected == 'move':
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
						delprop = self.GetPropUnderMouse(p)
						if isinstance(delprop, Platform):
							# make sure there's at least one platform level in this level
							if len(self.level.layer.platforms) == 1:
								delprop = None
								self.levelmanager.AddMessage("Last platform!", callback=None, time=2)
						if delprop:
							# unset the player's last platform since it will no longer exist
							if delprop == self.level.player.lastplatform:
								self.level.player.lastplatform = None
							# unset the player's current platform since it will no longer exist
							if delprop == self.level.player.platform:
								self.level.player.platform = None
							self.level.layer.RemoveProp(delprop)
				elif type(self.selected) is not str:
					# selected in a tool object not a string
					#pos = [int(x * gfx.width) for x in p]
					self.selected.OnMouseDown(e.pos)				
	
	@editOn
	def MouseMove(self, e):
		bitmapPos = [int(x * gfx.width) for x in self.level.camera.FromScreenCoordinates(e.pos)]
	
		if self.rect:
			# portal has a maximum size
			if self.selected == 'portal':
				self.rect.SetCorner(e.pos, (0.05, 0.05))
			else:
				self.rect.SetCorner(e.pos)
		elif self.selected in ('move', 'clone') and self.down and self.currentSurface and self.currentSurface != self.level:
			self.currentSurface.Drag(self.level.camera.FromScreenCoordinates(e.pos))
		elif type(self.selected) is not str:
			self.selected.OnMouseMove(e.pos)
		
		if hasattr(self.level.camera, "FromScreenCoordinates"):
			# do the hover mode thing - show the names of objects
			p = self.level.camera.FromScreenCoordinates(e.pos)
			hover = self.GetPropUnderMouse(p)
			# if we have moused over a new edit layer thing
			if hover != self.lastHover:
				self.lastHover = hover
				# remove the edit-field on the chatbox
				if isinstance(hover, Item) and hover.visible:
					self.levelmanager.hud.chatBox.ShowText(hover.description, self.UpdateItemDescription)
				else:
					self.levelmanager.hud.chatBox.RevertText()
					
		self.mouseMovePosition = bitmapPos
	
	@editOn
	def MouseUp(self, e):
		self.down = False
		if self.rect:
			if abs(self.rect[2]) > 0.002 and abs(self.rect[3]) > 0.002:
				if self.selected in ['platform', 'portal', 'item']:
					self.rect.Absolute()
					self.level.Create(self.selected, {'rectangle': list(self.rect)})
			self.Remove(self.rect)
		self.rect = None
		if self.currentSurface:
			self.currentSurface.MouseUp()
			self.currentSurface = None
		if type(self.selected) is not str:
			self.selected.OnMouseUp([int(x * gfx.width) for x in self.level.camera.FromScreenCoordinates(e.pos)])

