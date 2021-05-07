# Load Balancer
# Tabish Jabir

import socket
import os
import datetime
import signal
import sys
import argparse
import time
import random

# Constant for our buffer size

BUFFER_SIZE = 1024

# Server socket timeout setting in seconds (300 seconds = 5 minutes)

TIMEOUT = 300

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
    elif value == '301':
        message = message + value + ' Permamently Moved\r\n' + date_string + '\r\n' 
    return message

# Send the given response and file back to the client.

def send_response_to_client(sock, code, file_name, location = 'no_location'):

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
    if (code == '301'):
        header = prepare_response_message(code) + 'Location: ' + location + '\r\nContent-Type: ' + type + '\r\nContent-Length: ' + str(file_size) + '\r\n\r\n'
    else:
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
    while (not done):
        char = sock.recv(1).decode()
        if (char == '\r'):
            pass
        elif (char == '\n'):
            done = True
        else:
            line = line + char
    return line

# prepare a get message

def prepare_get_message(host, port, file_name):
    request = f'GET {file_name} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n' 
    return request

# connect to a set of servers, if the connection fails remove the servers from the server list

def connect_to_servers(client_sockets,server_array,server_list):
    i = 0
    while(i < len(server_array)):
        try:
            client_sockets.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
            client_sockets[i].connect((server_list[i][0], int(server_list[i][1])))
        except ConnectionRefusedError:
            print('Error: ' + server_array[i] + ' is not accepting connections. Removing.')
            client_sockets.pop(i)
            server_array.pop(i)
            server_list.pop(i)
            continue
        except IndexError: break
        i = i + 1

# test a set of servers for their performance and store the response times

def performance_test(server_array,server_list,preferSum,probabilities,timers,client_sockets):
    i = 0
    while(i < len(server_array)):
        message = prepare_get_message(server_list[i][0],int(server_list[i][1]),"test.txt") 
        timer1 = time.perf_counter()
        client_sockets[i].send(message.encode())  
        client_sockets[i].recv(BUFFER_SIZE)
        timer2 = time.perf_counter()
        probabilities.append(timer2-timer1)
        timers[i,0] = timer2-timer1
        timers[i,1] = "unmarked"
        preferSum = preferSum + i + 1
        i = i + 1
    return preferSum

# create a list of probabilities based on the performance ranking of a list of servers

def create_probabilities(server_array,timers,timersAsc,probabilities,preferSum):
    x = 0
    while(x < len(server_array)):
        i = 0
        while(i < len(server_array)):
            if((timers[i,0] == timersAsc[x]) and (timers[i,1] != "marked")): 
                probabilities[i] = (len(server_array) - x) / preferSum
                timers[i,1] = "marked"
            i = i + 1
        x = x + 1

# turn the first column of an (a,b) tuple dictionary into an array

def get_timer_array(server_array,timers):
    i = 0 
    replaceTimers = []
    while(i < len(server_array)):
        replaceTimers.append(timers[i,0])
        i = i +1
    return replaceTimers

# print the results of a performance test

def print_performance(server_array,timers,probabilities):
    print('----------PERFORMANCE INFORMATION:--------')
    print("Number of Servers: " + str(len(server_array)))
    print("Servers: ")
    print(server_array)
    print("Request times: ")
    print(timers)
    print("Probabilities: ")
    print(probabilities) 


# Our main function.

def main():

    # Register our signal handler for shutting down.
    signal.signal(signal.SIGINT, signal_handler)

    # initialize the command line argument parser

    parser = argparse.ArgumentParser()
    parser.add_argument('-servers',help = 'Type in a set of servers in the form hostname:portnumber with a space between each.', type = str)
    args = parser.parse_args()

    # parse the servers from the command line and store the information in arrays

    try:
        servers = args.servers
        server_array = servers.split("/") 
        server_list = []
        i = 0
        while(i < len(server_array)):
            serverInfo = server_array[i].split(":")
            server_list.append([serverInfo[0],serverInfo[1]])
            i = i + 1   
    except:
        print('Error. Invalid input for servers option. Enter one or more servers of the form hostName:portNumber, and place a "/" between seperate servers.')    
        sys.exit(1)

    # create client sockets to servers and remove a server from the list of servers if it is not responding
    
    client_sockets = []
    connect_to_servers(client_sockets,server_array,server_list)
    
    # close the balancer if there are no servers in the server list
    
    if(len(server_array) == 0): 
                print("This load balancer associates with no servers. Closing.")
                sys.exit(1)      

    # test each server for its response time using a test file and store the times in a dictionary
    
    preferSum = 0
    probabilities =[]
    timers = {}
    preferSum = performance_test(server_array,server_list,preferSum,probabilities,timers,client_sockets)
        
    # create an ascending sorted list of the times as a ranked list
    
    timersAsc = sorted(probabilities)

    # create a list of probabilities for each server based on their rank in the list
    
    create_probabilities(server_array,timers,timersAsc,probabilities,preferSum)

    # create an array of response times from the dictionary of response times

    timers = get_timer_array(server_array,timers)

    # print the performance information

    print_performance(server_array,timers,probabilities)

    # Create the socket.  We will ask this to work on any interface and to pick
    # a free port at random.  We'll print this out for clients to use.

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', 0))
    
    # set the timeout for the server socket to 5 minutes (10 seconds is useful for testing)

    server_socket.settimeout(TIMEOUT)
    print('Will wait for client connections at port ' + str(server_socket.getsockname()[1]))
    server_socket.listen(1)

    # Keep the server running forever.

    while(1):

        print('-------------LOAD BALANCER----------------')    
        print('Waiting for incoming client connection ...')
        
        # have the balancer wait for a new client request

        try:
            conn, addr = server_socket.accept()
        
        # once the balancer times out start a new performance test

        except socket.timeout:

           # create client sockets to servers and remove a server from the list of servers if it is not responding
    
            client_sockets = []
            connect_to_servers(client_sockets,server_array,server_list)
            
            # close the balancer if there are no servers in the server list
            
            if(len(server_array) == 0): 
                        print("This load balancer associates with no servers. Closing.")
                        sys.exit(1)      

            # test each server for its response time using a test file and store the times in a dictionary
            
            preferSum = 0
            probabilities =[]
            timers = {}
            preferSum = performance_test(server_array,server_list,preferSum,probabilities,timers,client_sockets)
                
            # create a sorted list of the times as a ranked list
            
            timersAsc = sorted(probabilities)

            # create a list of probabilities for each server based on their rank in the list
            
            create_probabilities(server_array,timers,timersAsc,probabilities,preferSum)

            # create an array of response times from the dictionary

            timers = get_timer_array(server_array,timers)

            # print the performance information

            print_performance(server_array,timers,probabilities)

            # return to waiting for a connection

            continue
        
        # continue to processing the request if there is a client request
        
        print('Accepted connection from client address:', addr)
        print('Connection to client established, waiting to receive message...')

        # We obtain our request from the socket.  We look at the request and
        # figure out what to do based on the contents of things.

        request = get_line_from_socket(conn)
        print('Received request:  ' + request)
        request_list = request.split()

        # This server doesn't care about headers, so we just clean them up.

        while (get_line_from_socket(conn) != ''):
            pass

        # If we did not get a GET command respond with a 501.

        if request_list[0] != 'GET':
            print('Invalid type of request received ... responding with error!')
            send_response_to_client(conn, '501', '501.html')

        # If we did not get the proper HTTP version respond with a 505.

        elif request_list[2] != 'HTTP/1.1':
            print('Invalid HTTP version received ... responding with error!')
            send_response_to_client(conn, '505', '505.html')

        # We have the right request and version, so forward the client to its assigned server
                    
        else:

            # select the server randomly based on the weighted probabilities assigned to each server

            randomValue = random.choices(server_array, weights = probabilities)

            # create the url for the location line in the response message

            location = "http://" + randomValue[0] + "/" + request_list[1]

            # send 301 Permanently Moved response message to client

            send_response_to_client(conn,'301','301.html',location)
                
        # We are all done with this client, so close the connection and
        # Go back to get another one!

        conn.close();


if __name__ == '__main__':
    main()

