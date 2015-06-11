#!/urs/bin/env python

import sys
import socket
import datetime
import time
import select

class connection:
    '''
    class connection
    ----------------
    handles a connection from beginning to end
    init values:
        string  server
        int     port
        string  channel
        string  realname
        string  nickname
        string  ident
    '''
    def __init__(self, server, port, channel, realname, nickname, ident):
        self.SERVER = server
        self.PORT = port
        self.CHANNEL = channel
        self.REALNAME = realname
        self.NICKNAME = nickname
        self.IDENT = ident
        
    def connect(self):
        self.s = socket.socket()
        self.s.connect((self.SERVER, self.PORT))
        self.s.send('NICK ' + self.NICKNAME + '\n')
        self.s.send('USER ' + self.IDENT + ' ' + self.SERVER +' bla: ' + self.REALNAME + '\n')
        
    def listen(self):
        lines = []
        stub = ''
        '''
        this obviously cannot stay
        an infinite loop
        '''
        while True:
            stream = self.s.recv(2048)
            print stream,
            time.sleep(1)
        self.s.close()

if __name__ == '__main__':
    server = 'chat.freenode.net'
    port = 6667
    channel = '#5'
    realname = 'ateloph test'
    nickname = 'ateloph_test'
    ident = 'posiputt'
    freenode = connection(server, port, channel, realname, nickname, ident)
    freenode.connect()
    freenode.listen()