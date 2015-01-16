import socket
import sys


# Constants
SERVER = 'chat.freenode.net'
PORT = 6667
REALNAME = NICK = "ateloph_posi"
IDENT = "posiputt"

'''
Secure shutdown: 
The method closes the socket and flushes the buffer to the log.
Input: Socket socket, String msg, List buf
Outcome: Quits program.
'''
def shutdown(socket, msg, buf):
    socket.close()
    with  open('log', 'a') as out:
        out.write(buf+'\n')
    out.close()
    print msg
    sys.exit("Exiting. Log has been written.")
    

# connect to server
def conbot():
    s = socket.socket()
    s.connect((SERVER, PORT))
    s.send('NICK ' + NICK + '\n')
    s.send('USER ' + IDENT + ' ' + SERVER +' bla: ' + REALNAME + '\n')
    return s
    
if __name__ == '__main__':
    s = conbot()
    
    # Generate a List line and List "buffer" buf.
    buf = line = s.recv(500)
    print line

    try:
        while True:
            line = s.recv(500)
            buf += line # log all the lines!
            print line

            #join AFTER connect is complete
            if line.find('Welcome to the freenode') != -1:
                s.send('JOIN #5\n')

            # rude quit command (from anyone)
            if line.find('hau ab') != -1:
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
                
    except Exception as e:
        shutdown(s, e, buf)
        raise e

