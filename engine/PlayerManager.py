from PodSix.Config import config

from PodSixNet.Connection import ConnectionListener

from engine.Player import Player

class PlayerManager(ConnectionListener):
	""" Mixin used by Core.py to manage all the other player instances. """
	def __init__(self, game):
		self.game = game
		# player.remoteID => player
		self.players = {}
	
	def Pump(self):
		ConnectionListener.Pump(self)
	
	def ActivateAll(self):
		for p in self.players:
			self.players[p].Activate()
	
	###
	### Network events
	###
	
	def GetLevel(self):
		return self.game.levels[self.game.level]
	
	def Network_player_entering(self, data):
		config.debug('PlayerManager Got player ' + str(data))
		if not self.players.has_key(data['id']):
			p = Player(self.game, data['id'])
			self.GetLevel().AddCharacter(p)
			p.SetLevel(self.GetLevel())
			self.players[data['id']] = p
			p.Pump()
			self.UpdatePlayercount()
		else:
			print 'already have this player ID!'
	
	def Network_player_leaving(self, data):
		if self.players.has_key(data['id']):
			self.game.levels[self.game.level].RemoveCharacter(self.players[data['id']])
			del self.players[data['id']]
			self.UpdatePlayercount()
	
	def UpdatePlayercount(self):
		self.game.hud.playersLabel.SetPlayers(len(self.players))
	
	# when a leveldump is received (new leveldata from the server if we just joined a level)
	def Network_leveldump(self, data):
		if data['progress'] == "end":
			# tell the server we are now active
			self.game.net.SendWithID({"action": "activate"})
	
	# we have received a new block of players from a level we just joined, so activate them all
	def Network_playerdump(self, data):
		if data['progress'] == "end":
			self.ActivateAll()
	
	def Clear(self):
		for p in self.players:
			self.game.levels[self.game.level].RemoveCharacter(self.players[p])
		self.players = {}

