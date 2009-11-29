from PodSix.Resource import *
from PodSix.GUI.TextInput import TextInput

class ChatBox(TextInput):
	def __init__(self, parent):
		self.parent = parent
		self.specials = [8, 9, 13]
		TextInput.__init__(self, {"left": 0.01, "bottom": 0.55}, 0.8, "/help", dict([(x, chr(x)) for x in range(97, 122)]), font="chat")
	
	def KeyDown(self, e):
		self.Draw()
		if self.textWidth < self.width * gfx.width  - self.letterWidth and not e.key in self.specials:
			#print e.key
			self.text += e.unicode

