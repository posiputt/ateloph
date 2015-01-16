import socket

# secure shutdown:
# close socket, show message, append buffer to log file
def shutdown(socket, msg, buf):
    socket.close()
    out = open('log', 'a')
    out.write(buf+'\n')
    out.close()
    print msg
    quit()

SERVER = 'chat.freenode.net'
PORT = 6667
NICK = "ateloph_posi"
IDENT = "posiputt"
REALNAME = NICK

# connect to server
s = socket.socket()
s.connect((SERVER, PORT))
s.send('NICK ' + NICK + '\n')
s.send('USER ' + IDENT + ' ' + SERVER +' bla: ' + REALNAME + '\n')

line = s.recv(500)
print line
# log first line into buffer
buf = line

while True:
    line = s.recv(500)
    buf += line # log all the lines!
    print line

    #join AFTER connect is complete
    if line.find('Welcome to the freenode') != -1:
        s.send('JOIN #botophobia\n')

    # rude quit command (from anyone)
    if line.find('hau ab') != -1:
        shutdown(s, "ich geh ja schon", buf)

    # catch disconnect
    if line.find(':Closing Link:') != -1:
        shutdown(s, "connection lost", buf)

    line = line.rstrip()
#    print line
    line = line.split()
#    print line

    # pong if pinged
    if (line[0] == 'PING'):
        pong = 'PONG '+line[1]+'\n'
        print pong
        s.send(pong)
shutdown(s, "end of program", buf)
