import sys
from time import sleep
from random import choice, random, randint
from string import letters

from PodSix.Concurrent import Concurrent

from PodSixNet.Connection import connection, ConnectionListener

class NetMonitor(ConnectionListener, Concurrent):
	def __init__(self, parent):
		self.parent = parent
		Concurrent.__init__(self)
		# do we have a current connection with the server?
		self.serverconnection = 0
		self.playerID = None
		# randomly have an ID already (clients which have connected before)
		#if randint(0, 1) and len(self.demo_ids):
		#	self.playerID = self.demo_ids.pop()
		#	self.Send({"action": "playerid", "id": self.playerID})
		#else:
			# request a new UUID secret player ID to begin with
	
	def Connect(self, host):
		connection.DoConnect((host, 31415))
		self.Send({"action": "playerid"})
	
	def SendWithID(self, data):
		# send a data packet with this player's ID included, unless they don't have one
		# which should disconnect us from the server
		if self.playerID:
			data.update({"id": self.playerID})
		if self.serverconnection == 1:
			self.Send(data)
			return True
	
	def Disconnect(self):
		if self.serverconnection == 1:
			connection.Close()
		self.serverconnection = 2
	
	def Pump(self):
		connection.Pump()
		ConnectionListener.Pump(self)
		Concurrent.Pump(self)
	
	#######################################
	### Network event/message callbacks ###
	#######################################
	
	def Network(self, data):
		print "Received:", data
	
	def Network_playerid(self, data):
		# got my player ID, now send a new level i want to be on
		self.playerID = data['id']
		#self.SendWithID({"action": "setlevel", "level": choice(self.levels)})
	
	def Network_player_entering(self, data):
		print self.playerID, "Saw player with ID %d" % data['id']
	
	# built in stuff
	
	def Network_connected(self, data):
		self.serverconnection = 1
	
	def Network_error(self, data):
		self.serverconnection = 2
		connection.Close()
	
	def Network_disconnected(self, data):
		self.serverconnection = 2

