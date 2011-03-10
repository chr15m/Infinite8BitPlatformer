try:
	# psyco does not exist on 64 bit platforms
	import psyco
	psyco.full()
except ImportError:
	print "Psyco not available"
	pass

from server.I8BPServer import I8BPServer, SendExceptionEmail

#host, port = sys.argv[1].split(":")
host = "0.0.0.0"
port = 31415

s = I8BPServer(localaddr=(host, int(port)))
try:
	s.Launch()
except:
	SendExceptionEmail()

