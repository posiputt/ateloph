import socket

s = socket.socket()
with s.connect(('chat.freenode.net', 6667)):
    s.send('NICK ateloph_aos\n')

    s.send('USER ateloph_aos irc.freenode.net bla: atelophbot\n')

    while True:
        line = s.recv(500)
        print line
        if line.find('Welcome to the freenode') != -1:
            s.send('JOIN #5\n')
        if line.find('PRIVMSG') != -1:
            line = line.rstrip()
            line = line.split()
        if (line[0] == 'PING'):
            s.send('PONG '+line[1]+'\n')
