import sys
from time import sleep

from PodSixNet.Connection import connection, ConnectionListener

class TestClientException(Exception):
	pass

class TestClient(ConnectionListener):
	def __init__(self, host, port):
		self.Connect((host, port))
		print "TestClient started"
		self.playerID = None
		# request a new UUID secret player ID to begin with
		# TODO: sometimes randomly send some other data that i am not allowed to send yet
		self.Send({"action": "playerid"})
	
	def SendWithID(self, data):
		# send a data packet with this player's ID included
		if not self.playerID:
			raise TestClientException("I don't have a playerID yet")
		else:
			data.update({"id": self.playerID})
			self.Send(data)
	
	def SendRandomActivity(self):
		# randomly generate some activity, move, or chat and send it to the server
		pass
	
	#######################################
	### Network event/message callbacks ###
	#######################################
	
	def Network(self, data):
		print "Received:", data
	
	def Network_playerid(self, data):
		# got my player ID, now send a new level i want to be on
		# TODO: sometimes randomly send some other data/request
		print "Setting unique, secret player ID to %s" % data['id']
		self.playerID = data['id']
		self.SendWithID({"action": "setlevel", "level": "test level"})
	
	def Network_player_entering(self, data):
		print "Saw player with ID %d" % data['id']
	
	# built in stuff
	
	def Network_connected(self, data):
		print "Connected to the server"
	
	def Network_error(self, data):
		print 'error:', data['error'][1]
		connection.Close()
	
	def Network_disconnected(self, data):
		print 'Server disconnected'
		exit()

host = "localhost"
port = 31415
c = TestClient(host, int(port))
while 1:
	connection.Pump()
	c.Pump()
	sleep(0.001)

