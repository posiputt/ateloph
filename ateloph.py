"""
Atheloph: an IRC bot that writes a log.

TODOs:
 DONE) implement proactive ping so bot knows if it's disconnected
 DONE) implement auto-reconnect
    3) HTML logs with one anchor per line (or write a separate script to convert text to html)
    4) NICK and TOPIC functions

    0) regularly tidy up code!
"""

import socket
import sys
import datetime
import time
import select

# Commands for controlling the bot inside a channel
BOT_QUIT = "hau*ab"

# Constants
SERVER = 'chat.freenode.net'
PORT = 6667
REALNAME = "ateloph"
NICK = ["ateloph", "atel0ph", "ate1oph", "ate10ph"]
IDENT = "posiputt"
CHAN = "#5"
# ENTRY_MSG = 'Beep boop, wir testen den logbot. Wer ihn loswerden will, schreibe "' + BOT_QUIT + '".' 
# INFO = "Das Log ist derzeit sowieso nicht oeffentlich, sondern auf posiputts Rechner. Wer neugierig auf die sources ist oder mitmachen will, siehe hier: https://github.com/posiputt/ateloph"
ENTRY_MSG = 'entry.'
INFO = 'info.'
FLUSH_INTERVAL = 3 # num of lines to wait between log buffer flushes
CON_TIMEOUT = 260.0
PT_PAUSE = 10 # sleep time before reconnecting after ping timeout

log_enabled = False

'''
Secure shutdown: 
The method closes the socket and flushes the buffer to the log.
Input: Socket socket, String msg, List buf
Outcome: Quits program.
'''
def shutdown(socket, msg, buf):
    socket.close()
    buf = flush_log(buf)
    print msg
    sys.exit("Exiting. Log has been written.")

'''
Flush log:
save current buffer to file, return empty buffer to avoid redundancy
Input: String buf
Return: empty String buf
'''
def flush_log(buf):
    #print 'flushing log buffer to file'
    now = datetime.datetime.today()
    with open(str(now.date()) +'.log', 'a') as out:
        #print "in with-statement"
        out.write(buf)
        #print "written to file"
    out.close()
    #print "file closed"
    buf = ""
    #print "buf reset"
    return buf

# connect to server
def conbot(connects):
    s = socket.socket()
    s.connect((SERVER, PORT))
    s.send('NICK ' + NICK[connects%len(NICK)] + '\n')
    s.send('USER ' + IDENT + ' ' + SERVER +' bla: ' + REALNAME + '\n')
    return s
    
# Parser to get rid of irrelvant information
def parse(line):
    '''
    log_privmsg
    format IRC PRIVMSG for log
    input: string timestamp, string nickname, list words
    return: string logline
    '''
    def log_privmsg(timestamp, nickname, words):
        #print "in log_privmsg"
        words[3] = words[3][1:]         # remove the leading colon
        message = ' '.join(words[3:])
        logline = ' '.join([timestamp, nickname+':' , message])
        #print "log_privmsg ended"
        return logline

    '''
    log_join
    format IRC JOIN for log
    input: string timestamp, string nickname, list words
    return: string logline
    '''
    def log_join(timestamp, nickname, words):
        #print "in log_join"
        channel = words[2]
        logline = ' '.join([timestamp, nickname, 'joined', channel])
        #print "log_join ended"
        return logline

    '''
    log_quit
    format IRC QUIT for log
    input: string timestamp, string nickname, list words
    return: string logline
    '''
    def log_quit(timestamp, nickname, words):
        #print "in log_quit"
        #channel = words[2]
        logline = ' '.join([timestamp, nickname, 'left', CHAN])
        #print "log_part ended"
        return logline

    functions = {
            'PRIVMSG':  log_privmsg,
            'JOIN':     log_join,
            'QUIT':     log_quit,
            'PART':     log_quit
    }

    out = ''
    #print line
    words = line.split()

    timestamp = datetime.datetime.today().strftime("%H:%M:%S")
    nickname = words[0].split('!')[0][1:]
    #print nickname
    indicator = words[1]
    
    try:
        l = functions[indicator](timestamp, nickname, words)
        #print l
        out = l + '\n'
    except Exception as e:
        print 'Exception in parse - failed to pass to any appropriate function: ' + str(e)
    return out
    
def main():
    '''
    initializations
    '''
    recv_time = time.time() # time of most recent data from socket
    s = socket.socket()
    line = ''               # data from socket
    line_tail = ''          # helper to deal with cropped lines
    loglines = ''           # lines to be written to the log file
    reconnect = True
    connects = 0
    joined = False          # True if bot is in a channel
    run = True
    buf = []                # data from socket split by EOL
    
    try:
        while run:
            clean_eol = False
            log_enabled = False
            timestamp = datetime.datetime.today().strftime("%H:%M:%S")
            '''
            detect connection loss
            try to reconnect
            '''
            if time.time() - recv_time > CON_TIMEOUT:
                print "connection lost."
                reconnect = True
                print "set reconnect: True"
                joined = False
                print "set joined: False"
                loglines += timestamp + ' Connection lost.\n'
            if reconnect:
                try:
                    s.close()
                    print "socket closed"
                except Exception as recon_e:
                    print "Exception trying to reconnect: " + str(e)
                print "connecting ..."
                s = conbot(connects)
                connects += 1
                s.setblocking(0) # needet for the select below
                reconnect = False
                print "set reconnect: False"
                loglines += timestamp + ' Connecting to ' + SERVER + '\n'
            '''
            avoid reconnect spam
            '''
            s_ready = select.select([s], [], [], 10)
            if s_ready:
                '''
                avoid 'resource temporarily not available' error
                because of s.setblocking(0) above
                '''
                try:
                    line = line_tail + s.recv(2048)
                    recv_time = time.time()
                except:
                    line = ''
                buf = line.split('\n')
                '''
                avoid line stubs
                '''
                if line[-1:] == '\n':
                    clean_eol = True
                if not clean_eol:
                    line_tail = buf.pop(-1)
                '''
                answer PINGs from server,
                separate the internal junk from lines for the log file
                '''
                for b in buf:
                    if b == '':
                        continue
                    # print b
                    words = b.split(' ')
                    if words[0] == 'PING':
                        pong = 'PONG ' + words[1] + '\n'
                        #print pong
                        s.send(pong)
                        continue
                    '''
                    anything above this point should not go into the log file
                    '''
                    log_enabled = True
                    if not joined and words[1] == '376':
                        s.send('JOIN ' + CHAN + '\n')
                        joined = True
                        print "set joined: True"
                    if log_enabled:
                        loglines += parse(b)
            else:
                reconnect = True
            if log_enabled:
                loglines = flush_log(loglines)
    except Exception as main_e:
        print "Exception in main(): " + str(main_e)
        shutdown(s, main_e, loglines)
        raise main_e
    
if __name__ == '__main__':
    main()

