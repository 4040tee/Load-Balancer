A sample client and server solution to Assignment #2. 

server
------

To run the server, simple execute:

  python server.py

potentially substituting your installation of python3 in for python depending
on your distribution and configuration.  The server will report the port 
number that it is listening on for your client to use.  Place any files to 
transfer into the same directory as the server.

client
------

To run the client, execute:

  python client.py http://host:port/file - proxy host:port

where host is where the server is running (e.g. localhost), port is the port 
number reported by the server where it is running and file is the name of the 
file you want to retrieve.  Again, you might need to substitute python3 in for
python depending on your installation and configuration.

cache
-----------
To run the cache execute:

python cache.py