import socket
import os
import datetime
import signal
import sys
import datetime
from datetime import timezone, timedelta
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

    header = prepare_response_message(code) + 'Content-Type: ' + type + '\r\nContent-Length: ' + str(file_size) + '\r\n\r\n'
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
        elif (char == '\n' and 'Host:' not in line):
            done = True
        elif(char == '\n' and 'Host:' in line):
            doneCount = doneCount + 1
        else:
            line = line + char
        if doneCount == 2: done = True
    return line

#read a complete response from beginning to end and return it

def get_line_from_socket_CLIENTSIDE(sock):

    done = False
    line = ''
    doneCount = 0
    while (not done):
        char = sock.recv(1).decode()
        if (char == '\n'):
            doneCount = doneCount + 1
            line = line + char
        else:
            line = line + char
        if doneCount == 5: done = True
    return line   

#receive a file from the cache-client socket and send to the client

def send_file_from_socket(clientsock,serversock, bytes_to_read,output):
    
    i = 0
    length = len(output)
    while(i < length):
        chunk = output
        serversock.send(chunk)
        i = i + BUFFER_SIZE
        
    bytes_read = 0
    while (bytes_read < bytes_to_read):
        chunk = clientsock.recv(BUFFER_SIZE)
        bytes_read += len(chunk)
        serversock.send(chunk)

#save a file from the server via the client socket

def save_file_from_socket(sock, bytes_to_read, file_name):

    with open(file_name, 'wb') as file_to_write:
        bytes_read = 0
        while (bytes_read < bytes_to_read):
            chunk = sock.recv(BUFFER_SIZE)
            bytes_read += len(chunk)
            file_to_write.write(chunk)

#create a CONDITIONAL GET message

def prepare_conditional_get_message(host, port, file_name, date_created):
    request = f'GET {file_name} HTTP/1.1\r\nHost: {host}:{port}\r\nIf-modified-since: {date_created}\r\n\r\n' 
    return request
    
#print a file from the server via the client socket
    
def print_file_from_socket(sock, bytes_to_read):
    
    bytes_read = 0
    while (bytes_read < bytes_to_read):
        chunk = sock.recv(BUFFER_SIZE)
        bytes_read += len(chunk)
        print(chunk.decode()) 

#create a GET message

def prepare_get_message(host, port, file_name):
    request = f'GET {file_name} HTTP/1.1\r\nHost: {host}:{port}\r\n \r\n' 
    return request
        
def get_bytes_to_read(response_list):
    x = 0
    bytes_to_read = 0
    while (x < len(response_list)):
        if(response_list[x].startswith('Content-Length:')):
            Length_line = response_list[x].split(' ') 
            bytes_to_read = int(Length_line[1])
            break
        x = x + 1
    return bytes_to_read

def get_bytes_and_response(clientsock):
    bytes_to_read = 0
    headers_done = False
    while (not headers_done):
            header_line = get_line_from_socket(clientsock)
            print(header_line)
            header_list = header_line.split(' ')
            if (header_line == ''):
                headers_done = True
            elif (header_list[0] == 'Content-Length:'):
                print('CONTENT LENGTH HERE:')
                print(header_list[1])
                bytes_to_read = int(header_list[1])
    return bytes_to_read

# Our main function.

def main():

    #set the expiry date of the cache, default to 2 minutes (can be changed by minutes = , or hours = , or seconds =)
    expiryTime = timedelta(seconds = 30)

    #create a reference to the server's directory (to reset the directory after adding/removing files)
    cache_Directory = os.getcwd()

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
        
        # get server's host name and port number

        hostLine = get_line_from_socket(conn)
        hostLine = hostLine.replace('Host: ', '')
        hostList = hostLine.split(':')
        hostName = hostList[0]
        portNum = int(hostList[1])
        #print(hostName + ' ' + str(portNum)) 

        #create a client socket connecting to the server

        print('Connecting to server ...')
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((hostName, portNum))
        except ConnectionRefusedError:
            print('Error:  That host or port is not accepting connections.')
            sys.exit(1)

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

            #create an array containing the path of the file, and from it take the file name

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


            #create a name for the server's folder in the cache directory (format: host_port)
                
            serverFolder = hostName + '_' + str(portNum)

            # Check if requested file exists

            #if the file doesn't exist try to get it from the server

            if (not os.path.exists(os.getcwd() + '/' + serverFolder + req_file)):
                
                
                message = prepare_get_message(hostName, portNum, req_file)
                client_socket.send(message.encode())
                #print('sent GET message')
                
                # Receive the response from the server and start taking a look at it

                response_line = get_line_from_socket_CLIENTSIDE(client_socket)
                output = response_line
                response_list = response_line.split('\n')
                #print(response_line)
                #print(response_list[0])
                
                    
                # If an error is returned from the server, forward the 404 HTML file to the client to print
                
                if response_list[0].split(' ')[1] != '200':
                    print('Error:  An error response was received from the server.  Details:\n')
                    print(output)
                    bytes_to_read = 0
                    conn.send(response_line.encode())
                    bytes_to_read = get_bytes_and_response(client_socket)
                    send_file_from_socket(client_socket,conn, bytes_to_read,output)

                #if the server has the file retrieve it and send it to the client

                else:
                    print('Success:  Server is sending file.  Downloading it now.')
                    print(output)

                    #try to create the folder's in the file path, if they already exist shift the directory along the file path

                    try:
                        os.mkdir(serverFolder)
                        os.chdir(serverFolder)
                    except: os.chdir(serverFolder)
                    
                    i = 1
                    while(i < (len(path_list) - 1)):
                        try:
                            os.mkdir(path_list[i])
                            os.chdir(path_list[i])
                        except: os.chdir(path_list[i])
                        i = i + 1
                   
                   #send a 200 OK HTML response to the client along with the requested file
            
                    bytes_to_read = 0
                    
                    bytes_to_read = get_bytes_and_response(client_socket)
                    save_file_from_socket(client_socket, bytes_to_read, path_file)    
                    send_response_to_client(conn,'200',path_file)
                
                #close the client socket connecting to the server
                
                client_socket.close()
            
            #If the file exists, check it for expiration, or being out-of-date

            else:

                #shift into the file directory

                os.chdir(serverFolder)
                i = 1
                while(i < (len(path_list) - 1)):
                    os.chdir(path_list[i])
                    i = i + 1

                #get the timestamp of when the file was created

                created_date = datetime.datetime.fromtimestamp(os.path.getctime(path_file)).astimezone()

                #check if the file has expired, if so try to get a new file from the server

                if(datetime.datetime.now().astimezone() > created_date + expiryTime):
                    
                    print('The file is expired')

                    #remove the original file

                    os.remove(path_file)

                    #send a GET message to the server

                    message = prepare_get_message(hostName, portNum, req_file)
                    client_socket.send(message.encode())

                    # Receive the response from the server and start taking a look at it

                    response_line = get_line_from_socket(client_socket)
                    output = response_line
                    response_list = response_line.split(' ')
                        
                    #If the file does not exist in the server directory, forward the 404 message to the client

                    print(response_list[1])
                    if response_list[1] != '200':
                        
                        print('Error:  An error response was received from the server.  Details:\n')
                        print(output)
                
                        bytes_to_read = 0
                        conn.send(response_line.encode())
                        bytes_to_read = get_bytes_and_response(client_socket)
                        
                        send_file_from_socket(client_socket,conn, bytes_to_read,output)

                    #if the request was successful retrieve the file and forward it the client

                    else:
                        print('Success:  Server is sending file.  Downloading  and transferring it now.')
                        print(output)
                        # Go through headers and find the size of the file, then save it.
                
                        bytes_to_read = 0
                        
                        bytes_to_read = get_bytes_and_response(client_socket)
                        save_file_from_socket(client_socket, bytes_to_read, path_file)    
                        send_response_to_client(conn,'200',path_file)
                    
                    #close the client socket connecting to the server
                    client_socket.close()

                #if the file is NOT expired, check to see if it is out-of-date with the servers version
                
                else:

                    #convert the files creation time stamp into a string 

                    created_date = datetime.datetime.fromtimestamp(os.path.getctime(path_file)).astimezone().strftime('%a, %d %b %Y %H:%M:%S %Z')

                    #send a CONDITIONAL GET message to the server

                    message = prepare_conditional_get_message(hostName,portNum,req_file,created_date)
                    client_socket.send(message.encode())
                   
                    # Receive the response from the server and start taking a look at it

                    response_line = get_line_from_socket(client_socket)
                    output = response_line
                    response_list = response_line.split(' ')
                        

                    #print('PRINT----------------------')
                    #print(response_list[1])

                    #if the file is up-to-date, then send the file currently in the cache to the client
                    
                    if response_list[1] == '304':
                        print('Server file not modified. Details:')
                        print(output)
                        bytes_to_read = get_bytes_and_response(client_socket)
                        print_file_from_socket(client_socket, bytes_to_read)
                        send_response_to_client(conn,'200',path_file)

                    #if the request is successful retrieve the file and forward it to the client

                    elif response_list[1] == '200' :
                        
                        print('Success:  Server is sending file.  Downloading it now.')
                        print(output)
                        # Go through headers and find the size of the file, then save it.
                        os.remove(path_file)
                        bytes_to_read = 0
                        bytes_to_read = get_bytes_and_response(client_socket)
                        save_file_from_socket(client_socket, bytes_to_read, path_file)    
                        send_response_to_client(conn,'200',path_file)

                    # If an error is returned from the server, forward the error message to the client

                    else:
                        print('Error:  An error response was received from the server.  Details:')
                        print(output)
                        bytes_to_read = 0
                        conn.send(response_line.encode())
                        bytes_to_read = get_bytes_and_response(client_socket)
                        send_file_from_socket(client_socket,conn, bytes_to_read,output)


                    #close the client socket connecting to the server
                    client_socket.close()

                    
                
        os.chdir(cache_Directory)    
        # We are all done with this client, so close the connection and
        # Go back to get another one!

        conn.close()
    

if __name__ == '__main__':
    main()

