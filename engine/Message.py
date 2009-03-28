from PodSix.Concurrent import Concurrent
from PodSix.GUI.Label import Label
from PodSix.GUI.Button import TextButton

class Message(Concurrent):
	def __init__(self, parent):
		self.parent = parent
		Concurrent.__init__(self)
		self.lb = Label("", pos={"centerx": 0.5, "top": 0.25}, color=(255, 255, 255))
		self.tb = TextButton("ok >", pos={"right": 0.75, "top": 0.35}, colors=[(255, 255, 255), (77, 77, 77)])
		self.tb.Pressed = self.Pressed
		self.Add(self.tb)
		self.Add(self.lb)
		self.showing = False
	
	def Show(self, text):
		if self.showing:
			self.lb.text += "\n" + text
		else:
			self.lb.text = text
			self.parent.Add(self)
			self.showing = True
	
	def Hide(self):
		if self.showing:
			self.lb.text = ""
			self.parent.Remove(self)
			self.showing = False
	
	def Pressed(self):
		self.Hide()
		self.parent.ButtonOK()
	
