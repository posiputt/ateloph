"""
Atheloph: an IRC bot that writes a log.

TODOs:
    1) implement proactive ping so bot knows if it's disconnected
    2) implement auto-reconnect
    3) HTML logs with one anchor per line (or write a separate script to convert text to html)

    0) regularly tidy up code!
"""

import socket
import sys
import datetime
import time

# Commands for controlling the bot inside a channel
BOT_QUIT = "hau*ab"

# Constants
SERVER = 'chat.freenode.net'
PORT = 6667
REALNAME = NICK = "ateloph_posi"
IDENT = "posiputt"
CHAN = "#5"
# ENTRY_MSG = 'Beep boop, wir testen den logbot. Wer ihn loswerden will, schreibe "' + BOT_QUIT + '".' 
# INFO = "Das Log ist derzeit sowieso nicht oeffentlich, sondern auf posiputts Rechner. Wer neugierig auf die sources ist oder mitmachen will, siehe hier: https://github.com/posiputt/ateloph"
ENTRY_MSG = 'entry.'
INFO = 'info.'
FLUSH_INTERVAL = 3 # num of lines to wait between log buffer flushes
PING_TIMEOUT = 260.
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
    print 'flushing log buffer to file'
    now = datetime.datetime.today()
    with open(str(now.date()) +'.log', 'a') as out:
        print "in with-statement"
        out.write(buf)
        print "written to file"
    out.close()
    print "file closed"
    buf = ""
    print "buf reset"
    return buf    

# connect to server
def conbot():
    s = socket.socket()
    s.connect((SERVER, PORT))
    s.send('NICK ' + NICK + '\n')
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
        print "in log_privmsg"
        words[3] = words[3][1:]         # remove the leading colon
        message = ' '.join(words[3:])
        logline = ' '.join([timestamp, nickname+':' , message])
        print "log_privmsg ended"
        return logline

    '''
    log_join
    format IRC JOIN for log
    input: string timestamp, string nickname, list words
    return: string logline
    '''
    def log_join(timestamp, nickname, words):
        print "in log_join"
        channel = words[2]
        logline = ' '.join([timestamp, nickname, 'joined', channel])
        print "log_join ended"
        return logline

    '''
    log_part
    format IRC PART for log
    input: string timestamp, string nickname, list words
    return: string logline
    '''
    def log_part(timestamp, nickname, words):
        print "in log_part"
        channel = words[2]
        logline = ' '.join([timestamp, nickname, 'left', channel])
        print "log_part ended"
        return logline


    functions = {
            'PRIVMSG':  log_privmsg,
            'JOIN':     log_join,
            'PART':     log_part
    }

    out = ''
    print line
    words = line.split()
    print words
    if not words[0] == 'PING':
        timestamp = datetime.datetime.today().strftime("%H:%M:%S")
        nickname = words[0].split('!')[0][1:]
        print nickname
        indicator = words[1]
        
        try:
            l = functions[indicator](timestamp, nickname, words)
            print l
            return l + '\n'
        except Exception as e:
            print 'Exception in parse - failed to pass to any appropriate function: ' + str(e)
    return out
    
    
    
if __name__ == '__main__':
    s = conbot()
    
    # Generate a String "buffer" buf.
    ## Might be unecessary
    #buf = parse(s.recv(2048))

    try:
        i = 0 # counter for periodical flushing of buf
        buf = []
        loglines = ''  # for periodical flushing to the log file
        line_tail = '' # store incomplete lines (not ending with '\n') from the server here
        last_ping = time.time() # when did the server last ping us?
        print last_ping

        while True:
            clean_eol = False # 
            line = line_tail + s.recv(2048)
            line_tail = ''
            buf = line.split('\n')
            
            """
            does line end with clean EOL?
            (most times it won't)
            """
            if line[-1:] == '\n':
                clean_eol = True

            if not clean_eol:
                line_tail = buf.pop(-1)
            else:
                buf.pop(-1) # remove empty string from split

            #print "line populated"
            #buf += parse(line)
            #print "line parsed, back in main loop"
            for b in buf:
                loglines += parse(b)

            #join AFTER connect is complete
            if line.find('Welcome to the freenode') != -1:
                s.send('JOIN ' + CHAN + '\n')
                s.send('PRIVMSG ' + CHAN + ' :' + ENTRY_MSG + '\n')
                s.send('PRIVMSG ' + CHAN + ' :' + INFO + '\n')
                log_enabled = True

            # rude quit command (from anyone)
            if line.find(BOT_QUIT) != -1:
                s.send('PRIVMSG ' + CHAN + ' :ich geh ja schon\n')
                shutdown(s, "ich geh ja schon", buf)

            # catch disconnect
            if line.find(':Closing Link:') != -1:
                shutdown(s, "connection lost", buf)
            # catch ping timeout
            elif time.time() - last_ping > PING_TIMEOUT:
                last_ping = time.time()
                log_enabled = False
                print "Ping timeout!"
                s.close()
                for s in range(PT_PAUSE):
                    print s
                    time.sleep(1)
                print "Trying to reconnect"
                s = conbot()

            line = line.rstrip().split()
            #print line

            # Test method:
            # Bot should reply with 'pong' if 'ping'ed.
            if (line[0] == 'PING'):
                last_ping = time.time()
                pong = 'PONG '+line[1]+'\n'
                print pong
                s.send(pong)

            # flush log buffer to file, reset buffer and index
            i += 1
            print i
            if i > FLUSH_INTERVAL and log_enabled:
                loglines = flush_log(loglines)
                print "after buf = flush_log"
                i = 0
                
    except Exception as e:
        print "in main exception: " + str(e)
        shutdown(s, e, loglines)
        print "after shutdown"
        raise e

