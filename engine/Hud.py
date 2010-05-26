from os import path
import webbrowser

from PodSix.Resource import *
from PodSix.Concurrent import Concurrent
from PodSix.GUI.Button import ImageButton
from PodSix.GUI.Label import Label

from PodSixNet.Connection import ConnectionListener, connection

from engine.ChatBox import ChatBox

class EditButton(ImageButton):
	def __init__(self, parent):
		self.parent = parent
		ImageButton.__init__(self, [Image(path.join("resources", "icons", "back.png")), Image(path.join("resources", "icons", "back-invert.png"))], [24, 24])
	
	def Pressed(self):
		self.parent.Back()

class LevelNameLabel(Label):
	def __init__(self, parent):
		self.parent = parent
		self.editLayer = self.parent.game.editLayer
		Label.__init__(self, "Loading...", pos={"left": 0.1, "top": 0.02}, color=[255, 255, 255])
	
	def MouseOver(self, e):
		if self.editLayer.mode:
			self.parent.chatBox.ShowText(self.text, self.UpdateLevelName)
	
	def MouseOut(self, e):
		if self.editLayer.mode:
			self.parent.chatBox.RevertText()
	
	def UpdateLevelName(self, name):
		self.parent.game.SetLevelName(name)
		self.parent.chatBox.RevertText()

class FeedbackLink(Label):
	def __init__(self, parent):
		self.parent = parent
		Label.__init__(self, "bugs/feedback?", pos={"right": 0.85, "top": 0.02}, color=(255, 255, 255))
	
	def MouseOver(self, e):
		self.color = (255, 0, 0)
	
	def MouseOut(self, e):
		self.color = (255, 255, 255)
	
	def MouseDown(self, e):
		if self.InRect(e.pos):
			webbrowser.open("http://infiniteplatformer.com/feedback")

class ConnectedIcon(Concurrent, Image):
	def __init__(self, parent):
		self.parent = parent
		self.pos = [24, 396]
		Image.__init__(self, path.join("resources", "icons", "disconnected.png"))
		Concurrent.__init__(self)
	
	def Draw(self):
		print self.parent.game.net.serverconnection
		if not self.parent.game.net.serverconnection and (self.frame / 4) % 2:
			gfx.BlitImage(self, center=self.pos)

class Hud(Concurrent, EventMonitor, ConnectionListener):
	"""
	This layer holds the GUI for the player.
	"""
	def __init__(self, game):
		# whether edit mode is showing or not
		self.game = game
		Concurrent.__init__(self)
		EventMonitor.__init__(self)
		self.disconnectedIcon = ConnectedIcon(self)
		self.editButton = EditButton(self)
		self.chatBox = ChatBox(self, self.game.DoChatBox)
		self.levelLabel = LevelNameLabel(self)
		self.feedbacklink = FeedbackLink(self)
		# edit button turns on the other buttons
		self.Add(self.editButton)
		self.Add(self.chatBox)
		self.Add(self.levelLabel)
		self.Add(self.feedbacklink)
		self.Add(self.disconnectedIcon)
		self.priority = 2
	
	###
	###	Network events
	###
	
	def Network(self, data):
		print "Hud got network data:", data
	
	def Network_connected(self, data):
		print 'CONNECTED'
		self.serverconnection = 1
		self.game.AddMessage("Connected to the server", None, 5.0)
	
	def Network_error(self, data):
		self.game.AddMessage('error: ' + data['error'][1], None, 5.0)
		self.serverconnection = 2
		connection.Close()
	
	def Network_disconnected(self, data):
		self.serverconnection = 2
		self.game.AddMessage('disconnected from the server', None, 5.0)
	
	###
	###	Concurrency events
	###
	
	def Pump(self):
		ConnectionListener.Pump(self)
		Concurrent.Pump(self)
		EventMonitor.Pump(self)	
	
	def Update(self):
		Concurrent.Update(self)
	
	def Draw(self):
		Concurrent.Draw(self)
	
	def Back(self):
		self.game.Back()

