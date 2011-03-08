from os import path
from sys import platform
try:
	from simplejson import loads
except ImportError:
	from json import loads

class BuildFile:
	""" Stores all of the information about the current build being run. """
	def __init__(self):
		# this file is created by build.py for each platform
		buildfilename = path.join("resources", "build.json")
		if path.isfile(buildfilename):
			buildfile = file(buildfilename, "r")
			self.data = loads(buildfile.read())
			buildfile.close()
		else:
			# this is probably only installed if they are a developer
			try:
				from bzrlib.branch import Branch
				revno = Branch.open(".").revno()
			except:
				revno = "unknown"
			self.data = {"developer": True, "platform": platform, "revno": revno}
	
	def GetInfo(self):
		return self.data

buildfile = BuildFile()
