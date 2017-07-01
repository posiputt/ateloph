#!/usr/bin/env python3

import sys
import socket
import datetime
import time
import select
import codecs
import requests
import yaml
from lxml.html import fromstring

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
        string logfile       # Name of the file the content shall be written to
    '''
    def __init__(self, server, port, channel, realname, nickname, ident, cert_dir, logfile):
        self.SERVER = server
        self.PORT = port
        self.CHANNEL = channel
        self.REALNAME = realname
        self.numberOfReconnects = 0
        self.NICKNAME_BASE = nickname
        self.NICKNAME = self.NICKNAME_BASE + "[%i]" % self.numberOfReconnects
        self.IDENT = ident
        self.CERTDIR = cert_dir
        self.EOL = '\n'

        self.LOGFILE = logfile

        self.LOG_THIS = ['PRIVMSG', 'JOIN', 'PART', 'KICK', 'TOPIC']

        self.LASTPING = time.time()     # timeout detection helper
        self.PINGTIMEOUT = 600          # ping timeout in seconds
        self.CONNECTED = False          # connection status, init False


        self.buffer = ""
        self.now = datetime.datetime.now().strftime("%H:%M:%S")
        self.today = datetime.datetime.now().strftime("_%Y-%m-%d")

    def reconnect(self):
        try:
            if self.numberOfReconnects != 0:
                print("reconnecting attempt no. %i" % self.numberOfReconnects)
                self.socket.close()
                self.LASTPING = time.time()
                time.sleep(10)
            self.NICKNAME = self.NICKNAME_BASE + "[%i]" %self.numberOfReconnects
            self.CONNECTED = True
            self.connect()
            self.numberOfReconnects += 1
            print ("[CON] Connecting to " + self.SERVER)
        except Exception as e:
            self.CONNECTED = False
            print('[ERR] Something went wrong while connecting.'),
            raise e # Das will ich mir nachher nochmal anschauen. Musst die geraised werden? koennen wir uu exiten?

    def fill_buffer(self):
        empty_line = ""
        stream = self.buffer + self.listen(4096)
        if stream == empty_line:
            return
        lines = stream.split(self.EOL)
        print(lines)
        # As this result can be empty, we should use the[1-:] operator as
        # described at https://stackoverflow.com/questions/930397/getting-the-last-element-of-a-list-in-python#930398
        if lines[-1][-1:] != self.EOL:
            self.buffer = lines.pop(-1)
        else:
            self.buffer = ""
        return lines

    def run(self):
        while True:
            if not self.CONNECTED:
                self.reconnect()
            lines = self.fill_buffer()
            if lines is None:
                continue
            else:
                for line in lines:
                    print ("[RAW] " + line)
                    self.parse(line)

    def connect(self):
        self.socket = socket.socket()
        self.socket.connect((self.SERVER, self.PORT))
        connection_msg = []
        connection_msg.append('NICK ' + self.NICKNAME + self.EOL)
        connection_msg.append('USER ' + self.IDENT + ' ' + self.SERVER + ' bla: ' + self.REALNAME + self.EOL)
        self.socket.send(connection_msg[0].encode('utf-8'))
        self.socket.send(connection_msg[1].encode('utf-8'))

    def listen(self, chars):
        socket_ready = select.select([self.socket],[],[],10)
        if socket_ready:
            try:
                return self.socket.recv(chars).decode('utf-8')
            # Can we specify this error?
            except:
                print ("-p-o-s-s-i-b-l-y---LATIN 1---------------------")
                return self.socket.recv(chars).decode('latin-1')

    def sendPong(self, words):
        print (time.time() - self.LASTPING)
        self.LASTPING = time.time()
        pong = 'PONG ' + words[1] + self.EOL
        self.socket.send(pong.encode('utf-8'))
        print ("[-P-] " + pong)

    def parse(self, line):
        if line == '':
            if time.time() - self.LASTPING > self.PINGTIMEOUT:
                self.CONNECTED = False
                print ("PING timeout ... reconnecting")
            return
        words = line.split(' ')
        if words[0] == 'PING':
            self.sendPong(words)
        elif words[0][0] == ':':
            # def parseMessage
            words[0] = words[0][1:] # remove leading colon
            sender = words[0].split('!')
            nick = sender[0]
            indicator = words[1]
            channel = words[2]
            #def checkIndicator()
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
                for word in words[3:]:
                    # Dealing with leading spaces in the raw line by expanding them again.
                    if word == '':
                        message += " "
                    else:
                        self.expand_link(word, channel)
                        if message == '':
                            message = word
                        else:
                            message = " ".join((message, word)) #Wat? (())?
                '''
                logline will be written in the log file
                '''
                # Eventuell besser mit einem dictionary?
                # https://stackoverflow.com/questions/60208/replacements-for-switch-statement-in-python
                if indicator == 'PRIVMSG':
                    logline = " ".join((self.now, nick + ':', message))
                elif indicator == 'JOIN':
                    logline = " ".join((self.now, nick, 'joined', channel))
                elif indicator == 'PART':
                    logline = " ".join((self.now, nick, 'left', channel, message))
                elif indicator == 'TOPIC':
                    logline = " ".join((self.now, nick, 'set the topic to:', message))
                else:
                    logline = (self.now + " " + line)
                if not what_the_bot_said == '':
                    logline += self.EOL + self.NICKNAME+": " + what_the_bot_said 
                '''
                don't log IRC queries / private messages to the bot
                '''
                if not channel == self.NICKNAME:
                    with  codecs.open("web/" + self.LOGFILE + self.today + ".log", 'a', 'utf-8') as fName:
                        fName.write(logline + self.EOL)
                        self.today = datetime.datetime.now().strftime("_%Y-%m-%d")
                        self.now = datetime.datetime.now().strftime("%H:%M:%S")

            else:
                self.check_server_join_messages(indicator)

    def check_server_join_messages(self, indicator):
        # http://www.networksorcery.com/enp/protocol/irc.htm
        EndOfMOTD = "376"
        NickInUse = "433"
        if indicator == EndOfMOTD:
            self.join()
        elif indicator == NickInUse:
            self.CONNECTED = False

    def join(self):
        print ("[-J-] Joining " + self.CHANNEL)
        join_msg = 'JOIN ' + self.CHANNEL + self.EOL
        self.socket.send(join_msg.encode('utf-8'))
        
    def expand_link(self, word, channel):
        print ("potenzieller link: " + word)
        if (word.startswith("http://") or \
            word.startswith("https://")) and \
            len(word.split('.')) > 1:
            if not "192.168." in word:
                # title = self sendTitle()
                word = word[:-1]  # remove EOL
                try:
                    req = requests.get(word, verify=self.CERTDIR)
                    tree = fromstring(req.content)
                    title = tree.findtext('.//title')
                    post_to_chan = " ".join(("Page title:", title))
                    post_to_chan = post_to_chan.replace("\n", " ")
                # Again, is it a specific error?
                except requests.exceptions.SSLError:
                    print("SSL Error! Please check that the location of the certs in the config file is correct.")
                    post_to_chan = "Sorry, couldn't fetch page title. Please check that the location of the certs in the config file is correct."
                except:
                    post_to_chan = "Sorry, couldn't fetch page title."
                what_the_bot_said = post_to_chan
                post_to_chan = "PRIVMSG " + channel + " :" + post_to_chan + self.EOL
                print(post_to_chan)
                self.socket.send(post_to_chan.encode('utf-8'))
        else:
            pass

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

    try:
        freenode = Connection(
            config['server'],
            config['port'],
            config['channel'],
            config['realname'],
            config['nickname'],
            config['ident'],
            config['cert_dir'],
            config['log_file']
        )
    except KeyError as entry: # ohne 'as'? # keine ahnung, ich benutze exceptions so selten :D ich schreibe tatsaechlich auch gerade nur selten python.
        if entry == "log_file":
            Connection.logfile = config["channel"]
        else:
            exit("Error: Missing entry for {} in config file.".format(entry))

    if freenode != None:
        freenode.run()
    else:
        exit("Trying to create a connection failed. Please recheck your config file.")
