import sys
import socket
import string
import os

HOST = 'chat.freenode.org'
PORT = 6667
NICK = 'ateloph'
IDENT = 'ateloph'
REALNAME = 'ateloph_posi'
OWNER = 'posiputt'
CHANNELINIT = '#5'
readbuvver = ''

s = socket.socket()
s.connect((HOST, PORT))
s.send('NICK ' + NICK + 'n')
s.send('USER ' + IDENT + ' ' + HOST + ' bla :' + REALNAME + 'n')



while 1:
    line = s.recv(500)
    print line
    if line.find('Welcome to the freenode Internet Relay Chat Network')!=-1:
        s.send('JOIN' + CHANNELINIT + 'n')
    if line.find('PRIVMSG') != -1:
#        parsemsg(line)
        line = line.restrip()
        line = line.split()
        if(line[0] == 'PING'):
            s.send('PONG ' + line[1] + 'n')
