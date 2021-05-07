Instructions 
By: Tabish Jabir

server
------

To run the server, simply execute:

  python server.py

 Place any files to transfer into the same directory as the server.

client
------

To run the client, execute:

  python client.py http://host:port/file

  There are files supplied within the server directory called test.txt, test2.txt, and hardroncollider.jpg . test.txt is used for the performance test.

load balancer 
-------------

To the run the load balancer, execute:

	python balancer.py -servers host:port

For multiple servers add a "/" and enter the host:port for the additional server. For example, for three servers, execute:

	python balancer.py -servers host:port/host:port/host:port  

The timeout of the server can be adjusted through changing the TIMEOUT variable at the top of the program. 10 seconds is useful for testing,
though it is set to 5 minutes.


