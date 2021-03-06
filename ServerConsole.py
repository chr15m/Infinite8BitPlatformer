import sys
from time import sleep
from sys import stdin, exit
import code
import readline
import atexit
import os

from PodSixNet.Connection import connection, ConnectionListener
from PodSix.Config import config

# This example uses Python threads to manage async input from sys.stdin.
# This is so that I can receive input from the console whilst running the client connection.
# It's slow and ugly.
from threading import Thread
from Queue import Queue

import settings

config.SetFilename("Infinite8BitPlatformer.cfg")

# console based on Python's interactive console which supports history
class HistoryConsole(code.InteractiveConsole):
	def __init__(self, locals=None, filename="<console>",
				 histfile=os.path.expanduser("~/.I8BP-ServerConsole")):
		code.InteractiveConsole.__init__(self, locals, filename)
		self.init_history(histfile)
	
	def init_history(self, histfile):
		readline.parse_and_bind("tab: complete")
		if hasattr(readline, "read_history_file"):
			try:
				readline.read_history_file(histfile)
			except IOError:
				pass
			atexit.register(self.save_history, histfile)
	
	def save_history(self, histfile):
		readline.write_history_file(histfile)

class Console(ConnectionListener):
	def __init__(self, host, port):
		self.hostname = host
		self.Connect((host, port))
		print "I8BP console started"
		# fetch the player ID from infinite platformer config
		self.playerid = config.Get("playerID", default=None)
		print "using PlayerID:", self.playerid
		# pass results back to the input thread
		self.q = Queue()
		# launch our threaded input loop
		self.t = Thread(target=self.InputLoop, args=(self.q,))
		self.t.daemon = True
		self.t.start()
		# initiate the connection with our ID
		connection.Send({"action": "admin", "id": self.playerid})
	
	def Loop(self):
		connection.Pump()
		self.Pump()
		if not self.t.is_alive():
			sys.exit()
	
	def InputLoop(self, q):
		console = HistoryConsole(locals())
		# horrid threaded input loop
		# continually reads from stdin and sends whatever is typed to the server
		quit = False
		while not quit:
			print q.get(block=True),
			try:
				sendcommand = console.raw_input("I8BP:" + self.hostname + "> ")
				connection.Send({"action": "console", "command": sendcommand, "id": self.playerid})
			except EOFError:
				print
				quit = True
	
	#######################################
	### Network event/message callbacks ###
	#######################################
	
	def Network_result(self, data):
		self.q.put(data['result'])
	
	def Network_permission(self, data):
		print "Permission error: ", data['permission']
		exit()
	
	# built in stuff

	def Network_connected(self, data):
		self.q.put("You are now connected to the server\n")
	
	def Network_error(self, data):
		print 'error:', data['error'][1]
		exit()
	
	def Network_disconnected(self, data):
		print 'Server disconnected\n'
		exit()

host = len(sys.argv) >= 2 and sys.argv[1] or settings.SERVER_HOST
port = len(sys.argv) >= 3 and sys.argv[1] or 31415
c = Console(host, int(port))
while 1:
	c.Loop()
	sleep(0.001)

