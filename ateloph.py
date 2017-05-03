#!/usr/bin/env python3

import sys
import socket
import datetime
import time
import select
import requests
import codecs
from lxml.html import fromstring
import yaml
import sys

class Connection:
    '''
    class connection
    ----------------
    handles a connection from beginning to end
    init values:
        string  server      # irc server url to connect to
        int     port        # the port the server is listening on
        string  channel     # the channel the bot will log
        string  realname    # the bot's real name
        string  nickname    # the bot's nickname
        string  ident       # ident stuff whatever
    '''
    def __init__(self, server, port, channel, realname, nickname, ident, cert_dir):
        self.SERVER = server
        self.PORT = port
        self.CHANNEL = channel
        self.REALNAME = realname
        self.reconnects = 0
        self.NICKNAME_FIXED = nickname
        self.NICKNAME = self.NICKNAME_FIXED + "[%i]" % self.reconnects
        self.IDENT = ident
        self.CERTDIR = cert_dir
        self.EOL = '\n'

        self.LOG_THIS = ['PRIVMSG', 'JOIN', 'PART', 'KICK', 'TOPIC']

        self.LASTPING = time.time()     # timeout detection helper
        self.PINGTIMEOUT = 600          # ping timeout in seconds
        self.CONNECTED = False          # connection status, init False

    def run(self):
        run = True
        stub = ''
        while run:
            if not self.CONNECTED:
                try:
                    if not self.reconnects == 0:
                        print("reconnecting attempt no. %i" % self.reconnects)
                        self.s.close()
                        self.LASTPING = time.time()
                        time.sleep(10)
                    self.NICKNAME = self.NICKNAME_FIXED + "[%i]" % self.reconnects
                    self.CONNECTED = True
                    self.connect()
                    self.reconnects += 1
                    print ("[CON] Connecting to " + self.SERVER)
                except Exception as e:
                    self.CONNECTED = False
                    print ('[ERR] Something went wrong while connecting.'),
                    raise e
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
            if time.time() - self.LASTPING > self.PINGTIMEOUT:
                self.CONNECTED = False
                print ("PING timeout ... reconnecting")
            return
        words = line.split(' ')
        if words[0] == 'PING':
            print (time.time() - self.LASTPING)
            self.LASTPING = time.time()
            pong = 'PONG ' + words[1] + self.EOL
            self.s.send(pong.encode('utf-8'))
            print ("[-P-] " + pong)
        elif words[0][0] == ':':
            words[0] = words[0][1:] # remove leading colon
            sender = words[0].split('!')
            nick = sender[0]
            indicator = words[1]
            channel = words[2]
            if indicator in self.LOG_THIS:
                what_the_bot_said = ''
                message = ''
                '''
                this works like " ".join()
                except this keeps multiple spaces
                for stuff like ascii art
                '''
                if len(words) > 3:
                    words[3] = words[3][1:] # remove leading colon
                for w in words[3:]:
                    if w == '':
                        message += " "
                    else:
                        if (w.startswith("http://") or \
                        w.startswith("https://")) and \
                        len(w.split('.')) > 1:
                            if not "192.168." in w:
                                w = w[:-1]  # remove EOL
                                try:
                                    req = requests.get(w, verify = self.CERTDIR)
                                    tree = fromstring(req.content)
                                    title = tree.findtext('.//title')
                                    # post_to_chan = " ".join((title, w))
                                    post_to_chan = " ".join(("Page title:", title))
                                    post_to_chan = post_to_chan.replace("\n", " ")
                                    # print(post_to_chan)
                                except:
                                    post_to_chan = "Sorry, couldn't fetch page title."
                                what_the_bot_said = post_to_chan
                                post_to_chan = "PRIVMSG " + channel + " :" + post_to_chan + self.EOL
                                print(post_to_chan)
                                self.s.send(post_to_chan.encode('utf-8'))
                                #post_to_chan = ""
                            else:
                                pass
                            if message == '':
                                message = w
                            else:
                                message = " ".join((message, w))
                # cut leading colon
                # message = message[1:]
                '''
                logline will be written in the log file
                '''
                if indicator == 'PRIVMSG':
                    logline = " ".join((nick + ':', message, self.EOL))
                elif indicator == 'JOIN':
                    logline = " ".join((nick, 'joined', channel, self.EOL))
                elif indicator == 'PART':
                    logline = " ".join((nick, 'left', channel, message, self.EOL))
                elif indicator == 'TOPIC':
                    logline = " ".join((nick, 'set the topic to:', message, self.EOL))
                else:
                    logline = line
                if not what_the_bot_said == '':
                    logline += self.EOL + self.NICKNAME+": " + what_the_bot_said + self.EOL
                '''
                don't log queries
                '''
                if not channel == self.NICKNAME:
                    with  codecs.open('test', 'a', 'utf-8') as f:
                        f.write(logline + self.EOL)
                        f.close()
            else:
                if indicator == '376':
                    self.join()
                elif indicator == '433':
                    self.CONNECTED = False

    def join(self):
        print ("[-J-] Joining " + self.CHANNEL)
        join_msg = 'JOIN ' + self.CHANNEL + self.EOL
        self.s.send(join_msg.encode('utf-8'))

    def handle_indicator(indicator, line):
        if indicator not in self.LOG_THIS:
            return -1



# END OF class Connection


if __name__ == '__main__':
    try:
        script, config_file = sys.argv
        config = yaml.load(open(config_file))
    except ValueError:
        if len(sys.argv) < 2:
            exit("Please provide a configuration file as argument")
        elif len(sys.argv) > 2:
            exit("Please give only one argument")
        else:
            exit("Unknown Error")
    except FileNotFoundError:
        exit("Config file not found")

    freenode = Connection(
            config['server'],
            config['port'],
            config['channel'],
            config['realname'],
            config['nickname'],
            config['ident'],
            config['cert_dir']
    )
    freenode.run()
