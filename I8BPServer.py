from server.I8BPServer import I8BPServer

#host, port = sys.argv[1].split(":")
host = "0.0.0.0"
port = 31415

s = I8BPServer(localaddr=(host, int(port)))
s.Launch()

