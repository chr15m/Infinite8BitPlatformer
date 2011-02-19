from os import path
import sys
import traceback
import cStringIO
import webbrowser
import base64
import urllib
import gzip

from PodSix.Resource import *
from PodSix.Game import Game

from engine.NetMonitor import NetMonitorErrorException, NetMonitorDisconnectionException

class ExceptionHandler(Game, EventMonitor):
	def __init__(self):
		# before anything, fetch the exception that was thrown and it's value
		exctype, value = sys.exc_info()[:2]
		print exctype, value
		# now print the traceback out as per usual
		traceback.print_exc()
		self.ziptrace = None
		#sfx.LoadSound('splash')
		#sfx.PlaySound('splash')
		self.face = pygame.image.load(path.join(*["resources", "icons", "sad-invert.png"]))
		self.bgColor = (255, 255, 255)
		gfx.Caption('Infinite 8-bit Platformer')
		gfx.SetSize([640, 200])
		gfx.LoadFont("freaky_fonts_ca", 16.0 / gfx.width)
		# if this is not a known exception then we want the crashdump
		if not exctype in [NetMonitorErrorException, NetMonitorDisconnectionException]:
			value = "Argh, Infinite 8-Bit Platformer crashed! Click here to send us a crash-report so we can fix the bug. Thank you!"
			# now collect the value of the traceback into our file like object
			catcherror = cStringIO.StringIO()
			# wrap the error catcher in gzip
			traceback.print_exc(file=gzip.GzipFile(fileobj=catcherror, mode="w"))
			self.ziptrace = catcherror.getvalue()
		self.message = gfx.WrapText(str(value), 0.8)
		
		Game.__init__(self)
		EventMonitor.__init__(self)
	
	def Pump(self):
		Game.Pump(self)
		EventMonitor.Pump(self)
	
	def Run(self):
		gfx.screen.blit(self.face, [16, 16])
		for l in range(len(self.message)):
			gfx.DrawText(self.message[l], pos={"left": 0.1, "top": 0.05 + 0.05 * l}, color=[255, 255, 255])
		Game.Run(self)
		gfx.Flip()
	
	def KeyDown(self, e):
		self.Quit()
	
	def MouseDown(self, e):
		if self.ziptrace:
			webbrowser.open("http://infiniteplatformer.com/feedback?" + urllib.urlencode({"trace": base64.b64encode(self.ziptrace)}))
		self.Quit()

