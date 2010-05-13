import sys
from time import sleep
from random import choice, random, randint
from string import letters

from PodSixNet.Connection import connection, ConnectionListener

class TestClientException(Exception):
	pass

class TestClient(ConnectionListener):
	levels = ("test level", "bob", "hello")
	
	demo_ids = [
		'c9a32e14-5e5c-11df-bb07-0017f2ecb25d',
		'c69aa666-5e5c-11df-bb07-0017f2ecb25d',
		'c7d2d7b0-5e5c-11df-bb07-0017f2ecb25d',
		'c866b124-5e5c-11df-bb07-0017f2ecb25d',
		'be1ccbb8-5e5c-11df-bb07-0017f2ecb25d',
	]
	
	moves = ("jump", "left", "right", "portal")
	
	activities = (
		# all of the different types of moves the user can make
		{"action": "move", "what": choice(moves), "position": (randint(-10, 1000), randint(-10, 1000)), "velocity": (random() * 2 - 1, random() * 2 - 1)},
		{"action": "chat", "message": "".join([choice(letters + " ") for x in range(randint(0, 256))])},
		# purposely horrible data
		{"GWAGERWGesgresgres": "gresgresgre!!!R#@R$#"},
	)
	
	def __init__(self, host, port):
		self.Connect((host, port))
		print "TestClient started"
		self.playerID = None
		# do we have a current connection with the server?
		self.serverconnection = 0
		# randomly have an ID already (clients which have connected before)
		if randint(0, 1) and len(self.demo_ids):
			self.playerID = self.demo_ids.pop()
			self.Send({"action": "playerid", "id": self.playerID})
		else:
			# request a new UUID secret player ID to begin with
			self.Send({"action": "playerid"})
	
	def SendWithID(self, data):
		# send a data packet with this player's ID included, unless they don't have one
		# which should disconnect us from the server
		if self.playerID:
			data.update({"id": self.playerID})
		self.Send(data)
	
	def SendRandomActivity(self):
		# randomly generate some activity, move, or chat and send it to the server
		self.SendWithID(choice(self.activities))
	
	def Disconnect(self):
		if self.serverconnection == 1:
			print self.playerID, 'disconnecting randomly'
			connection.Close()
		self.serverconnection = 2
	
	#######################################
	### Network event/message callbacks ###
	#######################################
	
	def Network(self, data):
		print self.playerID, "Received:", data
	
	def Network_playerid(self, data):
		# got my player ID, now send a new level i want to be on
		print "Setting unique, secret player ID to %s" % data['id']
		self.playerID = data['id']
		self.SendWithID({"action": "setlevel", "level": choice(self.levels)})
	
	def Network_player_entering(self, data):
		print self.playerID, "Saw player with ID %d" % data['id']
	
	# built in stuff
	
	def Network_connected(self, data):
		self.serverconnection = 1
		print self.playerID, "Connected to the server"
	
	def Network_error(self, data):
		print self.playerID, 'error:', data['error'][1]
		self.serverconnection = 2
		connection.Close()
	
	def Network_disconnected(self, data):
		self.serverconnection = 2
		print self.playerID, 'disconnected from the server'
		exit()

host = "localhost"
port = 31415
c = TestClient(host, int(port))
while c.serverconnection < 2:
	connection.Pump()
	c.Pump()
	# randomly send messages to the server
	# (this will sometimes happen when i'm not yet set up correctly, which is good)
	# (should trigger an exception which we ignore)
	if random() > 0.99:
		c.SendRandomActivity()
	# occasionally disconnect a client
	if random() > 0.9999:
		c.Disconnect()
	sleep(0.001)

