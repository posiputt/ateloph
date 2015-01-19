import socket
import sys
import datetime

# Constants
SERVER = 'chat.freenode.net'
PORT = 6667
REALNAME = NICK = "ateloph_test"
IDENT = "posiputt"
CHAN = "#freie-gesellschaft"
ENTRY_MSG = 'Beep boob, wir testen den logbot. Wer ihn loswerden will, schreibe "' + BOT_QUIT + '".' 
INFO = "Das Log ist derzeit sowieso nicht oeffentlich, sondern auf posiputts Rechner. Wer neugierig auf die sources ist oder mitmachen will, siehe hier: https://github.com/posiputt/ateloph"
FLUSH_DIST = 1 # num of lines to wait between log buffer flushes

# Commands for controlling the bot inside a channel
BOT_QUIT = "hau*ab"

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
    with open(now.date() +'log', 'a') as out:
        out.write(now.strftime("%H:%M:%S") + ': ' +buf+'\n')
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
def parser(line):
    pass
    
    
if __name__ == '__main__':
    s = conbot()
    
    # Generate a List line and List "buffer" buf.
    buf = line = s.recv(500)
    print line

    try:
        i = 0 # counter for periodical flushing of buf
        while True:
            line = s.recv(500)
            buf += line # log all the lines!
            print line

            #join AFTER connect is complete
            if line.find('Welcome to the freenode') != -1:
                s.send('JOIN ' + CHAN + '\n')
                s.send('PRIVMSG ' + CHAN + ' :' + ENTRY_MSG + '\n')

            # rude quit command (from anyone)
            if line.find(BOT_QUIT) != -1:
                s.send('PRIVMSG ' + CHAN + ' :ich geh ja schon\n')
                shutdown(s, "ich geh ja schon", buf)

            # catch disconnect
            if line.find(':Closing Link:') != -1:
                shutdown(s, "connection lost", buf)

            line = line.rstrip().split()
            print line

            # Test method:
            # Bot should reply with 'pong' if 'ping'ed.
            if (line[0] == 'PING'):
                pong = 'PONG '+line[1]+'\n'
                print pong
                s.send(pong)

            # flush log buffer to file, reset buffer and index
            i += 1
            if i > FLUSH_DIST:
                buf = flush_log(buf)
                i = 0
                
    except Exception as e:
        shutdown(s, e, buf)
        raise e

