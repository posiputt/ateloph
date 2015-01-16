import socket

s = socket.socket()
s.connect(('chat.freenode.net', 6667))
line = s.recv(500)
print "moop: " + line
s.send('NICK ateloph\n')
s.send('USER posiputt irc.freenode.net bla: atelophbot\n')

i = 0
while True:
    print i,
    i += 1
    line = s.recv(500)
    print line
    if line.find('Welcome to the freenode') != -1:
        s.send('JOIN #5\n')
    if line.find('PRIVMSG') != -1:
        line = line.rstrip()
        line = line.split()
        if (line[0] == 'PING'):
            pong = 'PONG'+line[1]+'\n'
            print pong
            s.send(pong)
