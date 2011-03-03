from random import randint
from sys import maxint, argv
from os import path
from uuid import uuid1

from PodSix.Resource import *
from PodSix.Concurrent import Concurrent
from PodSix.Rectangle import Rectangle
from PodSix.Config import config
from PodSix.GUI.Button import TextButton, ImageButton, ImageRadioButton, ImageRadioButtonGroup
from PodSix.Platformer.Item import Item
from PodSix.Platformer.Platform import Platform

from PodSixNet.Connection import ConnectionListener

from ColorPicker import ColorPicker
from BitLevel import BitLevel

import Tools

class EditBox(Rectangle, Concurrent):
	def __init__(self, inlist, camera, levelrect):
		self.initial = camera.FromScreenCoordinates(inlist)
		# make sure initial click is inside the level bounds
		for axis in (0, 1):
			self.initial[axis] = max(0, min(levelrect[2 + axis], self.initial[axis]))
		inlist = self.initial + [0, 0]
		Rectangle.__init__(self, inlist)
		Concurrent.__init__(self)
		self.camera = camera
		self.color = (255, 255, 255)
		self.levelrect = levelrect
	
	def Draw(self):
		gfx.DrawRect(self.camera.TranslateRectangle(self), self.color, 1)
	
	def SetWidth(self, val):
		self.Width(val)
	
	def SetHeight(self, val):
		self.Height(val)
	
	def SetCorner(self, pos, bounds=[maxint, maxint]):
		pos = self.camera.FromScreenCoordinates(pos)
		points = []
		# respect the bounds
		for axis in (0,1):
			points.append([self.initial[axis], max(self.initial[axis] - bounds[axis], min(pos[axis], self.initial[axis] + bounds[axis]))])
			points[-1].sort()
		self.Left(points[0][0])
		self.Width(points[0][1] - points[0][0])
		self.Top(points[1][0])
		self.Height(points[1][1] - points[1][0])
		# make sure we don't allow the edit rectangle to go bigger than the level size
		Rectangle.__init__(self, self.Clip(self.levelrect))

def editOn(fn):
	def newfn(self, *args, **kwargs):
		if self.mode and self.level:
			return fn(self, *args, **kwargs)
	return newfn

class PortalDestinationIcon(ImageButton):
	help_text = "portal destination"
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
	col = 0
	def __init__(self, name, parent, buttonGroup):
		self.parent = parent
		if name != "---":
			ImageRadioButton.__init__(self,
				[Image(path.join("resources", "icons", name + ".png")), Image(path.join("resources", "icons", name + "-invert.png"))],
				[gfx.width - 24 - self.__class__.col * 36, self.__class__.btncount * 36 + 64],
				name, buttonGroup)
			if self.__class__.col == 0:
				self.__class__.col = 1
			else:
				self.__class__.col = 0
				self.__class__.btncount += 1
			self.help_text = name
		else:
			self.__class__.col = 0
			self.__class__.btncount += 0.5
			
	
	def Draw(self):
		if self.name != '---':
			ImageButton.Draw(self)
	
	def Pressed(self):
		self.parent.selected = self.name
		self.parent.CallMethod("Pressed_" + self.name)

class NewButton(ImageButton):
	help_text = "new"
	def __init__(self, parent):
		self.parent = parent
		ImageButton.__init__(self, [Image(path.join("resources","icons", "new.png")), Image(path.join("resources", "icons", "new-invert.png"))], [gfx.width - 96, 24])
	
	def Pressed(self):
		self.parent.NewLevel()

class LockButton(ImageButton):
	help_text = "lock"
	def __init__(self, parent):
		self.parent = parent
		self.allow = False
		self.alts = [
			[Image(path.join("resources","icons", "lock-open-invert.png")), Image(path.join("resources", "icons", "lock-closed-invert.png"))],
			[Image(path.join("resources","icons", "lock-open.png")), Image(path.join("resources", "icons", "lock-closed.png"))],
		]
		ImageButton.__init__(self, self.alts[1 * self.allow], [gfx.width - 60, 24], toggle=True)
	
	def Set(self, locked, allow=None):
		if not allow is None:
			self.allow = allow
		self.down = locked
		self.images = self.alts[1 * self.allow]
	
	def MouseDown(self, e):
		if self.allow:
			ImageButton.MouseDown(self, e)
	
	def MouseUp(self, e):
		if self.allow:
			ImageButton.MouseUp(self, e)
	
	def Pressed(self):
		if self.allow:
			self.parent.ToggleLocked()

class EditButton(ImageButton):
	help_text = "edit"
	def __init__(self, parent):
		self.parent = parent
		ImageButton.__init__(self, [Image(path.join("resources", "icons", "edit.png")), Image(path.join("resources", "icons", "edit-invert.png"))], [gfx.width - 24, 24], toggle=True)
	
	def Pressed(self):
		self.parent.ToggleMode()

class EditInterface(Concurrent):
	pass

class EditLayer(Concurrent, EventMonitor, ConnectionListener):
	"""
	This layer holds the GUI for editing levels.
	The edit button always shows, but toggling it shows or hides the other stuff.
	"""
	def __init__(self, levelmanager):
		# whether edit mode is showing or not
		self.levelmanager = levelmanager
		self.game = levelmanager
		self.mode = False
		self.level = None
		self.editButton = EditButton(self)
		self.lockButton = LockButton(self)
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
		for b in ['platform', 'ladder', 'portal', 'item', '---', 'move', 'delete', 'clone']:
			FamilyButton(b, self, self.buttonGroup)
		
		self.pentool = Tools.PenTool(self, self.buttonGroup)
		self.linetool = Tools.LineTool(self, self.buttonGroup)
		self.filltool = Tools.FillTool(self, self.buttonGroup)
		self.airbrushtool = Tools.AirbrushTool(self, self.buttonGroup)
		# tools which remote users are currently using (created dynamically)
		self.networktools = {}
		
		# the save button
		self.editInterface.Add(NewButton(self))
		self.editInterface.Add(self.lockButton)
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
		self.loadProgress = 0
		
		# for some tools we need to know where the mouse button down event happened, so we can rubber band and the like...
		self.mouseDownPosition = [None,None]
		
		# for some tools, while the mouse is moving, we need to know the last mousemove pixel position. This stores that.
		# this way we can tell wether a mouse move actually moves through a large pixel to another
		self.mouseMovePosition = [None,None]
		
		# saved subimage for rubber banding
		self.savedImage = None
		
		# for line tool
		self.image_start = None
		
		# once we have received a level udpate from the server, we should tell the game about it
		self.startDest = None
	
	def MakeId(self):
		return 'prop-%s' % str(uuid1())
	
	def SetLevel(self, level):
		""" Called by LevelManager. """
		self.level = level
		self.level.SetEditLayer(self)
	
	def SetPortalDestination(self, destination):
		self.portalDestinationIcon.destination = destination
	
	def GetPortalDestination(self):
		return self.portalDestinationIcon.destination
	
	def ChangePortalDestination(self, portal, destination):
		self.RecordEdit({"action": "edit", "instruction": "portaldestination", "destination": destination, "objectid": portal.id})
		portal.destination = destination
	
	def UpdateItemDescription(self, description):
		self.RecordEdit({"action": "edit", "instruction": "itemdescription", "description": description, "objectid": self.lastHover.id})
		self.lastHover.description = description
		self.levelmanager.hud.chatBox.RevertText()
	
	def UpdateLevelName(self, name):
		# don't actually record or perform this update until we receive it back from the server 
		self.game.net.SendWithID({"action": "edit", "instruction": "levelname", "name": name})
		self.levelmanager.hud.chatBox.RevertText()
	
	def ToggleLocked(self):
		self.game.net.SendWithID({"action": "lock", "locked": self.lockButton.down})
	
	def ToggleMode(self):
		self.mode = self.editButton.down
	
	def SaveLevel(self):
		self.levelmanager.SaveLevel()
	
	def NewLevel(self):
		""" Request a new level from the server. """
		self.levelmanager.RequestNewLevel(self.ReceivedNewLevel)
	
	def ReceivedNewLevel(self, newlevel):
		# create a platform at the destination
		args = {'rectangle': [0.48, 0.495, 0.04, 0.01]}
		dest = newlevel.Create("platform", args)
		# teleport the player to the destination
		sfx.PlaySound("portal")
		self.levelmanager.SetLevel("level" + newlevel.name, dest.id)
		# send the creation of the portal over the network
		args.update({"action": "edit", "instruction": "create", "type": "platform", "objectid": dest.id})
		self.RecordEdit(args)
		#srcportal.destination = "level" + newlevel.name + ":" + destportal.id
		#player = self.levelmanager.player
		#srcportal = self.level.Create("portal", {'destination': "level" + newlevel.name + ":" + dest.id, 'rectangle': [player.rectangle.CenterX() - 0.01, player.GetBottom() - 0.03, 0.02, 0.03]})
		# create a portal at the destination too
		args = {'destination': "level" + self.level.name + ":start", 'rectangle': [0.49, 0.465, 0.02, 0.03]}
		destportal = newlevel.Create("portal", args)
		# send the portal creation commands over the network
		args.update({"action": "edit", "instruction": "create", "type": "portal", "objectid": destportal.id})
		self.RecordEdit(args)
		# save the new level we have created to our local cache
		self.levelmanager.SaveLevel()
		#srcportal.destination = "level" + newlevel.name + ":" + destportal.id
	
	def SetStartDest(self, dest):
		self.startDest = dest
	
	def On(self):
		return self.mode and self.level
	
	###
	###	Concurrency events
	###
	
	def Pump(self):
		ConnectionListener.Pump(self)
		if self.levelmanager.net.serverconnection == 1 and not self.game.hud.progress.showing:
			if self.On():
				self.editInterface.Pump()
				Concurrent.Pump(self)
				EventMonitor.Pump(self)
			else:
				self.editButton.Pump()
	
	def Update(self):
		if self.levelmanager.net.serverconnection == 1:
			if self.On():
				self.editInterface.Update()
				Concurrent.Update(self)
			else:
				self.editButton.Update()
	
	def Draw(self):
		if self.levelmanager.net.serverconnection == 1:
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
		if not len([o for o in self.editInterface.objects + self.objects + [p.icon for p in self.level.layer.portals] if hasattr(o, 'triggered') and o.triggered]):
			self.down = True
			if self.selected in ['platform', 'ladder', 'portal', 'item']:
				self.rect = EditBox(e.pos, self.level.camera, Rectangle([float(x) / gfx.width for x in self.level.sizerect]))
				self.Add(self.rect)
			else:
				p = self.level.camera.FromScreenCoordinates(e.pos)	
				if self.selected == 'move':
					self.currentSurface = self.GetPropUnderMouse(p)
					if self.currentSurface != self.level:
						self.currentSurface.Drag(p)
						self.RecordEdit({"action": "edit", "instruction": "startdrag", "pos": p, "objectid": str(self.currentSurface.id)})
				elif self.selected == 'clone':
					self.currentSurface = self.GetPropUnderMouse(p)
					if self.currentSurface != self.level:
						oldsurface = self.currentSurface
						self.currentSurface = self.level.Clone(self.currentSurface)
						self.currentSurface.Drag(p)
						self.RecordEdit({"action": "edit", "instruction": "clone", "pos": p, "objectid": str(oldsurface.id), "newobjectid": str(self.currentSurface.id)})
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
							self.RecordEdit({"action": "edit", "instruction": "delete", "objectid": str(delprop.id)})
				elif type(self.selected) is not str:
					# selected in a tool object not a string
					#pos = [int(x * gfx.width) for x in p]
					self.selected.OnMouseDown(e.pos)
	
	@editOn
	def MouseMove(self, e):
		if self.level.camera:
			bitmapPos = [int(x * gfx.width) for x in self.level.camera.FromScreenCoordinates(e.pos)]
			
			if self.rect:
				# portal has a maximum size
				if self.selected == 'portal':
					self.rect.SetCorner(e.pos, (0.05, 0.05))
				else:
					self.rect.SetCorner(e.pos)
			elif self.selected in ('move', 'clone') and self.down and self.currentSurface and self.currentSurface != self.level:
				dragpos = self.level.camera.FromScreenCoordinates(e.pos)
				self.currentSurface.Drag(dragpos)
				self.RecordEdit({"action": "edit", "instruction": "drag", "pos": dragpos, "objectid": str(self.currentSurface.id)})
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
				if self.selected in ['platform', 'ladder', 'portal', 'item']:
					self.rect.Absolute()
					newthing = self.level.Create(self.selected, {'rectangle': list(self.rect)})
					self.RecordEdit({"action": "edit", "instruction": "create", "type": self.selected, "rectangle": list(self.rect), "objectid": str(newthing.id)})
			self.Remove(self.rect)
		self.rect = None
		if self.currentSurface:
			self.currentSurface.MouseUp()
			self.RecordEdit({"action": "edit", "instruction": "stopdrag", "objectid": str(self.currentSurface.id)})
			self.currentSurface = None
		if type(self.selected) is not str:
			self.selected.OnMouseUp([int(x * gfx.width) for x in self.level.camera.FromScreenCoordinates(e.pos)])
	
	### Records an edit to the level history, and also to the network
	
	def RecordEdit(self, edit):
		self.level.AddHistory(edit)
		self.game.net.SendWithID(edit)
	
	###
	###	Network events
	###
	
	# when we are told whether we are an editor of this level and whether it is locked
	def Network_editor(self, data):
		self.lockButton.Set(data['locked'], data['editor'])
	
	def Network_lock(self, data):
		self.lockButton.Set(data['locked'])
	
	# when a leveldump is received (new leveldata from the server if we just joined a level)
	def Network_leveldump(self, data):
		# save the level if we have all the updated data
		if data['progress'] == "end":
			if self.startDest:
				self.game.GetOnStart(self.startDest)
				self.startDest = None
			if data['size']:
				self.game.SaveLevel()
				self.game.hud.progress.Hide()
		else:
			if data['size']:
				self.game.hud.progress.Show(data['size'])
				self.loadProgress = data['size']
	
	# when another player edits this layer
	def Network_edit(self, data):
		if "debug" in argv:
			print "edit data:", data
		if self.loadProgress:
			self.loadProgress -= 1
			self.game.hud.progress.Value(self.loadProgress)
		# record this in our level history
		self.level.AddHistory(data)
		# only perform this edit if we haven't seen it before
		if self.level.LastEdit() <= data['editid'] and data['level'] == "level" + self.level.id:
			# what edit instruction have we been sent?
			i = data.get('instruction', "")
			if i == "create":
				self.level.Create(data['type'], {'rectangle': list(data['rectangle']), "id": data['objectid']})
			elif i == "clone":
				newsurface = self.level.Clone(self.level.PropFromId(data['objectid']), data['newobjectid'])
				newsurface.Drag(data['pos'])
			elif i == "delete":
				delprop = self.level.PropFromId(data['objectid'])
				allplayers = self.levelmanager.players.players
				# check if any players have this as their last platform or platform
				for p in allplayers:
					# unset the player's last platform since it will no longer exist
					if delprop == allplayers[p].lastplatform:
						allplayers[p].lastplatform = None
					# unset the player's current platform since it will no longer exist
					if delprop == allplayers[p].platform:
						allplayers[p].platform = None
				# unset the player's last platform since it will no longer exist
				if delprop == self.level.player.lastplatform:
					self.level.player.lastplatform = None
				# unset the player's current platform since it will no longer exist
				if delprop == self.level.player.platform:
					self.level.player.platform = None
				self.level.layer.RemoveProp(delprop)
			# dragging objects around
			elif i == "startdrag":
				self.level.PropFromId(data['objectid']).Drag(data['pos'])
			elif i == "drag":
				self.level.PropFromId(data['objectid']).Drag(data['pos'])
			elif i == "stopdrag":
				self.level.PropFromId(data['objectid']).MouseUp()
			# drawing tools over the network
			elif i.startswith("pen"):
				if i == "pendown":
					# create the tool for this user
					self.networktools[data['id']] = getattr(Tools, data['tool'])(self)
					prop = self.level.PropFromId(data['objectid'])
					self.networktools[data['id']].NetworkPenDown(data['pos'], prop, data['color'])
				elif i == "penmove":
					self.networktools[data['id']].NetworkPenMove(data['pos'])
				elif i == "penup":
					self.networktools[data['id']].NetworkPenUp()
					del self.networktools[data['id']]
				elif i == "pendata":
					# some some special data for this tool
					self.networktools[data['id']].NetworkPenData(data)
			# name changes
			elif i == "levelname":
				self.levelmanager.SetLevelName(data['name'])
			elif i == "itemdescription":
				prop = self.level.PropFromId(data['objectid'])
				prop.description = data['description']
			elif i == "portaldestination":
				prop = self.level.PropFromId(data['objectid'])
				prop.destination = data['destination']
		else:
			print "dropped edit: ", data['editid'], "last:", self.level.LastEdit(), "levelid:", data['level'], "current:", "level" + self.level.id
