import sys
from time import sleep
from random import choice, random, randint
from string import letters

from PodSixNet.Connection import connection, ConnectionListener

class NetMonitor(ConnectionListener):
	def __init__(self, parent, host):
		self.parent = parent
		self.Connect((host, 31415))
		self.playerID = None
		# do we have a current connection with the server?
		self.serverconnection = 0
		# randomly have an ID already (clients which have connected before)
		#if randint(0, 1) and len(self.demo_ids):
		#	self.playerID = self.demo_ids.pop()
		#	self.Send({"action": "playerid", "id": self.playerID})
		#else:
			# request a new UUID secret player ID to begin with
		self.Send({"action": "playerid"})
	
	def SendWithID(self, data):
		# send a data packet with this player's ID included, unless they don't have one
		# which should disconnect us from the server
		if self.playerID:
			data.update({"id": self.playerID})
		self.Send(data)
	
	def Disconnect(self):
		if self.serverconnection == 1:
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

