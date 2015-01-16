import socket

def shutdown(socket, msg, buf):
    socket.close()
    out = open('log', 'a')
    out.write(buf+'\n')
    out.close()
    print msg
    quit()

s = socket.socket()
s.connect(('chat.freenode.net', 6667))
line = s.recv(500)
print "moop: " + line
s.send('NICK ateloph\n')
s.send('USER posiputt irc.freenode.net bla: atelophbot\n')

buf = line

for i in range(100):
    line = s.recv(500)
    buf += line
    print line
    if line.find('Welcome to the freenode') != -1:
        s.send('JOIN #botophobia\n')
    if line.find('hau ab') != -1:
        shutdown(s, "ich geh ja schon", buf)
    if line.find(':Closing Link:') != -1:
        shutdown(s, "connection lost", buf)
    line = line.rstrip()
    print line
    line = line.split()
    print line
    if (line[0] == 'PING'):
        pong = 'PONG '+line[1]+'\n'
        print pong
        s.send(pong)
shutdown(s, "end of program", buf)
