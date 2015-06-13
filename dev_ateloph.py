#!/usr/bin/env python2

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
        self.EOL = '\n'
        
    def run(self):
        print "[>] Connecting to " + self.SERVER
        try:
            self.connect()
        except Exception as e:
            print "[!] Error: " + str(e)
        stub = ''
        while True:
            stream = stub + self.listen(4096)
            lines = stream.split(self.EOL)
            if stream[-1] != self.EOL:
                stub = lines.pop(-1)
            else:
                stub = ''
            for l in lines:
                print "[RAW] " + l
                self.parse(l)
                
    def connect(self):
        self.s = socket.socket()
        self.s.connect((self.SERVER, self.PORT))
        self.s.send('NICK ' + self.NICKNAME + self.EOL)
        self.s.send('USER ' + self.IDENT + ' ' + self.SERVER +' bla: ' + self.REALNAME + self.EOL)
        
    def listen(self, chars):
        s_ready = select.select([self.s],[],[],10)
        if s_ready:
            return self.s.recv(chars)
    
    def parse(self, line):
        if line == '':
            return
        log_this = ['PRIVMSG', 'JOIN', 'PART', 'KICK', 'TOPIC']
        words = line.split(' ')
        if words[0] == 'PING':
            pong = 'PONG ' + words[1] + self.EOL
            self.s.send(pong)
            print "[P] " + pong
        elif words[0][0] == ':':
            sender = words[0]
            indicator = words[1]
            if indicator in log_this:
                channel = words[2]
                message = ' '.join(words[3:])
                print "[L] " + sender + ' ' + channel + ' ' + message
            else:
                if indicator == '376':
                    self.join()
    
    def join(self):
        print "[J] Joining " + self.CHANNEL
        self.s.send('JOIN ' + self.CHANNEL + self.EOL)
        

if __name__ == '__main__':
    server = 'chat.freenode.net'
    port = 6667
    channel = '#dumme-gesellschaft'
    realname = 'ateloph test'
    nickname = 'ateloph_test'
    ident = 'posiputt'
    freenode = connection(server, port, channel, realname, nickname, ident)
    freenode.run()