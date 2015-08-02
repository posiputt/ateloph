#!/usr/bin/env python3

import sys
import socket
import datetime
import time
import select

class Connection:
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
        run = True
        print ("[CON] Connecting to " + self.SERVER)
        try:
            self.connect()
        except Exception as e:
            print ('[ERR] Something went wrong while connecting.'),
            raise e
        stub = ''
        while run:
            stream = stub + self.listen(4096)
            if stream == '':
                continue
            #print (stream)
            lines = stream.split(self.EOL)
            if stream[-1] != self.EOL:
                stub = lines.pop(-1)
            else:
                stub = ''
            for l in lines:
                print ("[RAW] " + l)
                self.parse(l)
                
    def connect(self):
        self.s = socket.socket()
        self.s.connect((self.SERVER, self.PORT))
        connection_msg = []
        connection_msg.append('NICK ' + self.NICKNAME + self.EOL)
        connection_msg.append('USER ' + self.IDENT + ' ' + self.SERVER + ' bla: ' + self.REALNAME + self.EOL)
        self.s.send(connection_msg[0].encode('utf-8'))
        self.s.send(connection_msg[1].encode('utf-8'))
        
    def listen(self, chars):
        s_ready = select.select([self.s],[],[],10)
        if s_ready:
            try:
                return self.s.recv(chars).decode('utf-8')
            except: # Exception as e:
                return self.s.recv(chars).decode('latin-1')
                print ("-p-o-s-s-i-b-l-y---LATIN 1---------------------")
                # raise e
    
    def parse(self, line):
        if line == '':
            return
        log_this = ['PRIVMSG', 'JOIN', 'PART', 'KICK', 'TOPIC']
        words = line.split(' ')
        if words[0] == 'PING':
            pong = 'PONG ' + words[1] + self.EOL
            self.s.send(pong.encode('utf-8'))
            print ("[-P-] " + pong)
        elif words[0][0] == ':':
            sender = words[0]
            indicator = words[1]
            if indicator in log_this:
                channel = words[2]
                message = ' '.join(words[3:])
                # print ("[-L-] " + sender + ' ' + indicator + ' ' + channel + ' ' + message)
                line = ' '.join(("[-L-] ", sender, indicator, channel, message))
                print (line)
                with  open('test', 'a') as f:
                    f.write(line + self.EOL)
                    f.close()
            else:
                if indicator == '376':
                    self.join()
    
    def join(self):
        print ("[-J-] Joining " + self.CHANNEL)
        join_msg = 'JOIN ' + self.CHANNEL + self.EOL
        self.s.send(join_msg.encode('utf-8'))

# END OF class Connection
        

if __name__ == '__main__':
    server = 'chat.freenode.net'
    port = 6667
    channel = '#dumme-gesellschaft'
    realname = 'ateloph test'
    nickname = 'ateloph_test'
    ident = 'ateloph'
    freenode = Connection(server, port, channel, realname, nickname, ident)
    freenode.run()
