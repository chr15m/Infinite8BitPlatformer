# Tests out multiple simultaneous draw commands

import sys
from time import sleep
from random import choice, random, randint
from string import letters

from PodSixNet.Connection import connection, ConnectionListener

from server.version import VERSION

class TestClientException(Exception):
	pass

class TestClient(ConnectionListener):
	demo_ids = [
		'c9a32e14-5e5c-11df-bb07-0017f2ecb25d',
		'c69aa666-5e5c-11df-bb07-0017f2ecb25d',
		'c7d2d7b0-5e5c-11df-bb07-0017f2ecb25d',
		'c866b124-5e5c-11df-bb07-0017f2ecb25d',
		'be1ccbb8-5e5c-11df-bb07-0017f2ecb25d',
	]
	
	def __init__(self, host, port):
		print "TestClient started"
		self.playerID = None
		# do we have a current connection with the server?
		self.serverconnection = 0
		# have we started a draw command yet?
		self.pendown = False
		self.Connect((host, port))
	
	def SendWithID(self, data):
		# send a data packet with this player's ID included, unless they don't have one
		# which should disconnect us from the server
		if self.playerID:
			data.update({"id": self.playerID})
		self.Send(data)
		print "Sent:", data
	
	def SendRandomActivity(self):
		# randomly generate some activity, move, or chat and send it to the server
		#self.SendWithID(choice(self.activities))
		val = random()
		if val < 0.5:
			pass
		elif val > 0.9:
			self.SendWithID({'objectid': '2', 'color': (255, 255, 255), 'tool': 'LineTool', 'instruction': 'pendown', 'pos': [randint(450, 550), randint(175, 215)], 'action': 'edit'})
			self.pendown = True
		elif self.pendown:
			self.SendWithID({'action': 'edit', 'tool': 'LineTool', 'instruction': 'penmove', 'pos': [randint(450, 550), randint(175, 215)]})
		
	
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
		self.SendWithID({"action": "setlevel", "level": "level2", 'editid': 0})
	
	def Network_player_entering(self, data):
		print self.playerID, "Saw player with ID %d" % data['id']
	
	# built in stuff
	
	def Network_connected(self, data):
		self.serverconnection = 1
		print self.playerID, "Connected to the server"
		# randomly have an ID already (clients which have connected before)
		if randint(0, 1) and len(self.demo_ids):
			self.playerID = self.demo_ids.pop()
			self.Send({"action": "playerid", "id": self.playerID, "version": VERSION})
		else:
			# request a new UUID secret player ID to begin with
			self.Send({"action": "playerid", "version": VERSION})
	
	def Network_playerdump(self, data):
		if data['progress'] == "end":
			self.SendWithID({'action': 'move', 'velocity': [0, 0], 'move': 'StopRight', 'center': [0.25361501041192691, 0.51460409028957876]})
			self.SendWithID({'action': 'activate'})
	
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
	if c.serverconnection == 1 and random() > 0.99:
		c.SendRandomActivity()
	# occasionally disconnect a client
	if random() > 0.9999:
		c.Disconnect()
	sleep(0.001)

