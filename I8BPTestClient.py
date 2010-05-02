import sys
from time import sleep

from PodSixNet.Connection import connection, ConnectionListener

class TestClient(ConnectionListener):
	def __init__(self, host, port):
		self.Connect((host, port))
		print "TestClient started"
		connection.Send({"action": "playerid"})
	
	#######################################
	### Network event/message callbacks ###
	#######################################
	
	def Network_playerid(self, data):
		print "got:", data
	
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

