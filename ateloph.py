import socket
import sys
import datetime

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
        out.write(buf)
    out.close()
    buf = ""
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
        words[3] = words[3][1:]         # remove the leading colon
        message = ' '.join(words[3:])
        logline = ' '.join([timestamp, nickname+':' , message])
        return logline

    '''
    log_join
    format IRC JOIN for log
    input: string timestamp, string nickname, list words
    return: string logline
    '''
    def log_join(timestamp, nickname, words):
        channel = words[2]
        logline = ' '.join([timestamp, nickname, 'joined', channel])
        return logline

    '''
    log_part
    format IRC PART for log
    input: string timestamp, string nickname, list words
    return: string logline
    '''
    def log_part(timestamp, nickname, words):
        channel = words[2]
        logline = ' '.join([timestamp, nickname, 'left', channel])
        return logline


    functions = {
            'PRIVMSG':  log_privmsg,
            'JOIN':     log_join,
            'PART':     log_part
    }

    out = ""
    print line
    for l in line.split('\n'):
        if not l == '' and not l[:4] == 'PING':
            words = l.split(' ')
            timestamp = datetime.datetime.today().strftime("%H:%M:%S")

            '''
            nickname: remove leading colon,
            and user@domain
            '''
            nickname = words[0].split('!')[0][1:]
            indicator = words[1]

            try:
                l = functions[indicator](timestamp, nickname, words)
            except Exception as e:
                print 'Expception in parse - failed to pass to any appropriate fucntion: ' + str(e)

            print l
            return l+'\n'
    return out
    
    
    
if __name__ == '__main__':
    s = conbot()
    
    # Generate a String "buffer" buf.
    ## Might be unecessary
    #buf = parse(s.recv(2048))

    try:
        i = 0 # counter for periodical flushing of buf
        buf = ''
        while True:
            line = s.recv(2048)
            buf += parse(line)

            #join AFTER connect is complete
            if line.find('Welcome to the freenode') != -1:
                s.send('JOIN ' + CHAN + '\n')
                s.send('PRIVMSG ' + CHAN + ' :' + ENTRY_MSG + '\n')
                s.send('PRIVMSG ' + CHAN + ' :' + INFO + '\n')

            # rude quit command (from anyone)
            if line.find(BOT_QUIT) != -1:
                s.send('PRIVMSG ' + CHAN + ' :ich geh ja schon\n')
                shutdown(s, "ich geh ja schon", buf)

            # catch disconnect
            if line.find(':Closing Link:') != -1:
                shutdown(s, "connection lost", buf)

            line = line.rstrip().split()
            #print line

            # Test method:
            # Bot should reply with 'pong' if 'ping'ed.
            if (line[0] == 'PING'):
                pong = 'PONG '+line[1]+'\n'
                print pong
                s.send(pong)

            # flush log buffer to file, reset buffer and index
            i += 1
            if i > FLUSH_INTERVAL:
                buf = flush_log(buf)
                i = 0
                
    except Exception as e:
        shutdown(s, e, buf)
        raise e

