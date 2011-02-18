from os import path
import sys
import traceback

from PodSix.Resource import *
from PodSix.Game import Game

class ReportedException(Exception):
	pass

class ExceptionHandler(Game, EventMonitor):
	def __init__(self):
		# before anything, fetch the exception that was thrown and it's value
		exctype, value = sys.exc_info()[:2]
		print exctype, value
		# now print the traceback out as per usual
		traceback.print_exc()
		# now collect the value of the traceback into our file like object
		# traceback.print_exc(file=myfile)
		#sfx.LoadSound('splash')
		#sfx.PlaySound('splash')
		self.face = pygame.image.load(path.join(*["resources", "icons", "sad-invert.png"]))
		self.bgColor = (255, 255, 255)
		gfx.Caption('Infinite 8-bit Platformer')
		gfx.SetSize([640, 200])
		#gfx.SetSize([800, 450])
		gfx.LoadFont("freaky_fonts_ca", 16.0 / gfx.width, "default")
		self.message = str(value)
		#gfx.WrapText(self, text, maxwidth, font='default')
		Game.__init__(self)
		EventMonitor.__init__(self)
	
	def Pump(self):
		Game.Pump(self)
		EventMonitor.Pump(self)
	
	def Run(self):
		gfx.screen.blit(self.face, [16, 16])
		gfx.DrawText(self.message, pos={"left": 0.1, "top": 0.05}, color=[255, 255, 255])
		Game.Run(self)
		gfx.Flip()
	
	def KeyDown(self, e):
		self.Quit()
	
	def MouseDown(self, e):
		self.Quit()

