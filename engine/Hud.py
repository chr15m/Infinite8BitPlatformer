from os import path
import webbrowser

from PodSix.Resource import *
from PodSix.Concurrent import Concurrent
from PodSix.GUI.Button import ImageButton
from PodSix.GUI.Label import Label

from PodSixNet.Connection import ConnectionListener, connection

from engine.ChatBox import ChatBox

class BackButton(ImageButton):
	help_text = "back"
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
			self.parent.chatBox.ShowText(self.text, self.editLayer.UpdateLevelName)
	
	def MouseOut(self, e):
		if self.editLayer.mode:
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
		self.pos = [gfx.width - 24, 24]
		Image.__init__(self, path.join("resources", "icons", "disconnected.png"))
		Concurrent.__init__(self)
	
	def Draw(self):
		if self.parent.game.net.serverconnection != 1 and (self.frame / 10) % 2:
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
		self.backButton = BackButton(self)
		self.chatBox = ChatBox(self, self.game.DoChatBox)
		self.levelLabel = LevelNameLabel(self)
		self.feedbacklink = FeedbackLink(self)
		# edit button turns on the other buttons
		self.Add(self.backButton)
		self.Add(self.chatBox)
		self.Add(self.levelLabel)
		self.Add(self.feedbacklink)
		self.Add(self.disconnectedIcon)
		self.priority = 2
	
	###
	###	Network events
	###
	
	#def Network(self, data):
	#	print "Hud got network data:", data
	
	def Network_connected(self, data):
		self.game.AddMessage('Connected to ' + self.game.serverhost, None, 5.0)
	
	def Network_error(self, data):
		self.game.AddMessage('error: ' + data['error'][1], None, 5.0)
		if self.game.net.serverconnection:
			connection.Close()
	
	def Network_disconnected(self, data):
		self.game.AddMessage('Disconnected from ' + self.game.serverhost, None, 5.0)
	
	def Network_leveldump(self, data):
		if data['size']:
			if data['progress'] == "start":
				self.game.AddMessage("Receiving %d updates" % data['size'], None, 3.0)
			else:
				self.game.AddMessage("Done updating, saving level.", None, 3.0)
	
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

