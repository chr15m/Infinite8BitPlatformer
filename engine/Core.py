import webbrowser

from PodSix.Resource import *
from PodSix.Game import Game
from PodSix.Concurrent import Concurrent
from PodSix.Config import config
from PodSix.GUI.ToolTip import tooltip

from PodSixNet.Connection import ConnectionListener

from engine.Player import Player
from engine.Notification import Notification
from engine.EditLayer import EditLayer
from engine.Hud import Hud
from engine.BitCamera import BitCamera
from engine.LevelManager import LevelManager
from engine.NetMonitor import NetMonitor
from engine.PlayerManager import PlayerManager
from engine.Progress import Progress

class Core(Game, EventMonitor, LevelManager, ConnectionListener):
	def __init__(self, server="mccormick.cx"):
		self.serverhost = server
		config.zoom = 5
		self.bgColor = (255, 255, 255)
		gfx.Caption('Infinite 8-bit Platformer')
		gfx.SetSize([800, 450])
		gfx.LoadFont("freaky_fonts_ca", 16.0 / gfx.width, "default")
		gfx.LoadFont("FreeSans", 18.0 / gfx.width, "chat")
		gfx.LoadFont("FreeSansBold", 12.0 / gfx.width, "speech")
		#gfx.LoadFont("FreeSans", 8.0 / gfx.width, "tiny")
		sfx.LoadSound("item")
		sfx.LoadSound("portal")
		sfx.LoadSound("die")
		sfx.LoadSound("jump")
		Game.__init__(self)
		EventMonitor.__init__(self)
		# connection to the network
		self.net = NetMonitor(self)
		self.Add(self.net)
		# The editLayer user interface (hud for editing levels)
		self.editLayer = EditLayer(self)
		self.Add(self.editLayer)
		# The other hud stuff
		self.hud = Hud(self)
		self.Add(self.hud)
		# global tooltip singleton
		self.Add(tooltip)
		# progress bar should go above everything else
		self.progress = Progress()
		self.Add(self.progress)
		# set tooltip font
		#tooltip.font = "tiny"
		# Create player and camera and put some text on the screen
		#self.Setup("Infinite 8-bit Platformer\n\na game\nby Chris McCormick", self.Instructions, 1.0)
		self.Setup("Infinite 8-bit Platformer\n\na game\nby Chris McCormick", None, 3.0)
		# Give us the methods for manipulating level collections
		self.players = PlayerManager(self)
		LevelManager.__init__(self)
	
	def Launch(self):
		self.net.Connect()
		Game.Launch(self)
	
	#def Instructions(self):
	#	self.AddMessage("arrow keys move you\nenter key uses a portal\nescape key quits", None, 5.0)
	
	def Setup(self, message="", callback=None, time=None):
		# create our main player with id 0
		self.player = Player(self, 0, [0, 0, 11.0 / gfx.width, 12.0 / gfx.width], active=True)
		self.camera = BitCamera([0, 0, 1.0 / config.zoom, float(gfx.height) / gfx.width / config.zoom], tracking=self.player)
		if message:
			self.AddMessage(message, callback, time)
	
	def AddMessage(self, messagetxt, callback=None, time=None):
		# why do i have to do this? the first notification does not appear if I don't delay for 1 frame
		self.QueueLater(1, self.Add, Notification(self, messagetxt, callback=callback, time=time))
	
	def RemoveMessage(self, message):
		self.Remove(message)
	
	def Quit(self):
		Game.Quit(self)
	
	###
	### Concurrency
	###
	
	def Pump(self):
		ConnectionListener.Pump(self)
		self.players.Pump()
		Game.Pump(self)
		EventMonitor.Pump(self)
	
	def Run(self):
		if not self.level:
			gfx.SetBackgroundColor(self.bgColor)
		Game.Run(self)
		gfx.Flip()
	
	def Update(self):
		Concurrent.Update(self)
	
	###
	### Platformer events
	###
	
	def PlayerDied(self):
		# if they don't have a last platform them pick the first platform on the level
		destination = self.player.lastplatform and self.player.lastplatform.id or self.levels[self.level].layer.platforms[0].id
		self.QueueLater(100, self.JoinLevel, self.level, destination)
		self.LeaveLevel()
		self.Setup("oops!")
	
	def Teleport(self, portal):
		parts = portal.destination.split(":")
		if len(parts) == 2:
			self.SetLevel(portal=portal, *parts)
			return True
	
	def TeleportToLevel(self, displayName):
		if self.levels.get(displayName):
			levelname = self.levels[displayName].name
		else:
			levelname = displayName[len("level"):]
		self.SetLevel("level" + levelname, "start")
	
	def Back(self):
		LevelManager.Back(self)
	
	def DoChatBox(self, text):
		if text.startswith("/help"):
			webbrowser.open("http://infiniteplatformer.com/info/help")
		elif text.startswith("/teleport"):
			bits = text.split(" ")
			# TODO: support x,y locations and named portals
			destination = " ".join(bits[1:])
			matches = [l for l in self.levels if self.levels[l].displayName == destination]
			if len(matches):
				self.TeleportToLevel(matches[0])
			elif self.net.serverconnection == 1:
				self.net.SendWithID({"action": "findlevel", "name": destination})
			else:
				self.AddMessage("You are offline", None, 5.0)
		elif text.startswith("/new"):
			self.edit_layer.NewLevel()
		elif text.startswith("/quit"):
			self.Quit()
		elif text.startswith("/back"):
			self.Back()
		else:
			self.player.Chat(text)
			self.hud.chatBox.ClearText()
		self.hud.chatBox.Hide()
	
	###
	### Interface events
	###
	
	def KeyDown(self, e):
		#print e
		pass
	
	def KeyDown_escape(self, e):
		self.Quit()
	
	###
	### Network events
	###
	
	def Network_foundlevel(self, data):
		if data['level']:
			self.TeleportToLevel(data['level'])
		else:
			self.AddMessage('No such level "%s"' % data['name'], time=1)

