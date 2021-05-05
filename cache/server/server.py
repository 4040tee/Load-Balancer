import socket
import os
import datetime
import signal
import sys
from datetime import timezone,timedelta
import time


# Constant for our buffer size

BUFFER_SIZE = 1024

# Signal handler for graceful exiting.

def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    sys.exit(0)

# Create an HTTP response

def prepare_response_message(value):
    date = datetime.datetime.now()
    date_string = 'Date: ' + date.strftime('%a, %d %b %Y %H:%M:%S EDT')
    message = 'HTTP/1.1 '
    if value == '200':
        message = message + value + ' OK\r\n' + date_string + '\r\n'
    elif value == '404':
        message = message + value + ' Not Found\r\n' + date_string + '\r\n'
    elif value == '501':
        message = message + value + ' Method Not Implemented\r\n' + date_string + '\r\n'
    elif value == '505':
        message = message + value + ' Version Not Supported\r\n' + date_string + '\r\n'
    elif value == '304':
        message = message + value + ' File Not Modifiedr\r\n' + date_string + '\r\n'
    return message

# Send the given response and file back to the client.

def send_response_to_client(sock, code, file_name):

    # Determine content type of file

    if ((file_name.endswith('.jpg')) or (file_name.endswith('.jpeg'))):
        type = 'image/jpeg'
    elif (file_name.endswith('.gif')):
        type = 'image/gif'
    elif (file_name.endswith('.png')):
        type = 'image/jpegpng'
    elif ((file_name.endswith('.html')) or (file_name.endswith('.htm'))):
        type = 'text/html'
    else:
        type = 'application/octet-stream'
    
    # Get size of file

    file_size = os.path.getsize(file_name)

    # Construct header and send it

    header = prepare_response_message(code) + 'Content-Type: ' + type + '\r\nContent-Length: ' + str(file_size) + ' \r\n\r\n'
    sock.send(header.encode())

    # Open the file, read it, and send it

    with open(file_name, 'rb') as file_to_send:
        while True:
            chunk = file_to_send.read(BUFFER_SIZE)
            if chunk:
                sock.send(chunk)
            else:
                break

# Read a single line (ending with \n) from a socket and return it.
# We will strip out the \r and the \n in the process.

def get_line_from_socket(sock):

    done = False
    line = ''
    doneCount = 0
    while (not done):
        char = sock.recv(1).decode()
        if (char == '\r'):
            pass
        elif (char == '\n'):
            done = True
        else:
            line = line + char
    print(line)
    return line

# Our main function.

def main():
    
    Server_directory = os.getcwd()

    # Register our signal handler for shutting down.

    signal.signal(signal.SIGINT, signal_handler)

    # Create the socket.  We will ask this to work on any interface and to pick
    # a free port at random.  We'll print this out for clients to use.

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', 0))
    print('Will wait for client connections at port ' + str(server_socket.getsockname()[1]))
    server_socket.listen(1)
    
    # Keep the server running forever.
    
    while(1):
        print('Waiting for incoming client connection ...')
        conn, addr = server_socket.accept()
        print('Accepted connection from client address:', addr)
        print('Connection to client established, waiting to receive message...')

        # We obtain our request from the socket.  We look at the request and
        # figure out what to do based on the contents of things.

        request = get_line_from_socket(conn)
        print('Received request:  ' + request)
        request_list = request.split()
        
        # get server and host

        hostLine = get_line_from_socket(conn)
        hostLine = hostLine.replace('Host: ', '')
        hostList = hostLine.split(':')
        hostName = hostList[0]
        portNum = hostList[1]
        #print(hostName + ' ' + portNum) 

        #get creation time of file on the cache in the case of CONDITIONAL GET
        
        conditional_line = get_line_from_socket(conn)
        conditional_date = ''
        if conditional_line.startswith('If-modified-since:'):
            conditional_date = conditional_line.replace('If-modified-since: ','')
        #print(conditional_line)
        #print(conditional_date)

        # If we did not get a GET command respond with a 501.

        if request_list[0] != 'GET':
            print('Invalid type of request received ... responding with error!')
            send_response_to_client(conn, '501', '501.html')

        # If we did not get the proper HTTP version respond with a 505.

        elif request_list[2] != 'HTTP/1.1':
            print('Invalid HTTP version received ... responding with error!')
            send_response_to_client(conn, '505', '505.html')
        

        # We have the right request and version, so check if file exists.
                  
        else:

            #create an array containing the file path, and get the file name from it
            
            req_file = request_list[1]

            if '/' in req_file:
                path_list = req_file.split('/')
                path_file = path_list[len(path_list) - 1]
                
                """
                print(req_file)
                print(path_file)
                print(len(path_list))
                print(path_list[0])
                print(path_list[1])
                """

            # Check if requested file exists and report a 404 if not.

            if (not os.path.exists(os.getcwd() + req_file)):
                print('Requested file does not exist ... responding with error!')
                send_response_to_client(conn, '404', '404.html')

            #If the file exists check if it is out of date in the case of a conditional GET, otherwise simply send the file

            else:

                #move to the file directory
                
                i = 1
                while(i < (len(path_list) - 1)):
                    os.chdir(path_list[i])
                    i = i + 1
                

                #if it is a conditional get, check if the file is out of date, if not send a 304 HTML message, if so send the file

                if(conditional_date != ''):

                    #get the date of the latest modification of the file on the server

                    modified_date = datetime.datetime.fromtimestamp(os.path.getmtime(path_file))
                    
                    #convert the creation time of the file from the cache from a string to a datetime object

                    conditional_date = datetime.datetime.strptime(conditional_date,'%a, %d %b %Y %H:%M:%S %Z')

                    #check if the file is out of date and send a 304 message if not
                    
                    if(modified_date <= conditional_date):
                        print('File was not modified. Sending 304.')
                        os.chdir(Server_directory)
                        send_response_to_client(conn,'304','304.html')
                    
                    #send the file if it is out of date
                    
                    else:
                        os.chdir(Server_directory)
                        print('Requested file good to go!  Sending file ...')
                        send_response_to_client(conn, '200', path_file)
               
               #send the file in the case of a normal get request

                else:
                    os.chdir(Server_directory)
                    print('Requested file good to go!  Sending file ...')
                    send_response_to_client(conn, '200', path_file)

        os.chdir(Server_directory)

        # We are all done with this client, so close the connection and
        # Go back to get another one!

        conn.close();
    

if __name__ == '__main__':
    main()

