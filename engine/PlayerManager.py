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
	
	###
	### Network events
	###
	
	def GetLevel(self):
		return self.game.levels[self.game.level]
	
	def Network_player_entering(self, data):
		print 'PlayerManager Got player', data
		if not self.players.has_key(data['id']):
			p = Player(self.game, data['id'])
			self.GetLevel().AddCharacter(p)
			p.SetLevel(self.GetLevel())
			self.players[data['id']] = p
			p.Pump()
		else:
			print 'already have this player ID!'
	
	def Network_player_leaving(self, data):
		if self.players.has_key(data['id']):
			self.game.levels[self.game.level].RemoveCharacter(self.players[data['id']])
			del self.players[data['id']]
	
	def Clear(self):
		for p in self.players:
			self.game.levels[self.game.level].RemoveCharacter(self.players[p])
		self.players = {}

