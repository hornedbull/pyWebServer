ECEC 433 Mini-Project webServer
Vatsal Shah

Instructions to test:

1. Run the server using:
		python webserver.py #default port 22222
	or  python webserver.py 80 #to set a port

2. Open the browser of your choice (Safari, Firefox, Chrome, Opera, etc.):
	a. Go to: http://127.0.0.1:22222/index.html, fetches an html page with inline images from the server. Uses GET request
	b. Go to: http://127.0.0.1:22222/mini-project.pdf, opens the pdf in the default pdf plugin of the browser. Uses GET request
	c. Go to: http://127.0.0.1:22222/upload.html, fetches an upload page using GET request which has a form to upload a file. 
	Use the file placeholder to upload any .txt file (readme.txt) file to send a POST request to the server. The server echoes this text on stdout and also sends the browser back the plain text from the file.

Note: All the html files, image folders and readme.txt file are in the source folder. It is important to contain these files in the same folder as webserver.py, as index.html has path dependencies.

Project Highlights:

1. GET request can handle html files with inline images, jpg, png and pdf files. The handler is capable of parsing the requested path (for e.g. http://127.0.0.1:22222/path), where path corresponds to the directory where webserver.py is located. Any html, jpg, png or pdf file can be serviced to the client. Any GET/POST request can pretty much be serviced using the appropriate MIME types. The response codes are sent using the mimetools.messages contained in the baseHTTPRequestHandler class.

2. POST request can handle forms and file uploads. To test, included is an upload.html file used to POST a request to the server; which opens the file and sends the plain text contained back to the browser. This part is handled using the cgi class.
Note: All the socket errors are handled by the SocketServer.BaseServer class and the HTTP errors are handled by baseHTTPRequestHandler class. Other error catching like KeyboardInterrrupts is done outside of the subclasses.

3. The server is capable of maintaining the persistent connections in two ways:
	
	a. Optimized: The server listens to new quests in a non-blocking fashion and handles pending requests using select(). However, after a request is fulfilled, it jumps on to the next request on the select() keeping the connection open unless a Connection: close header was supplied by the client browser. This was done because most browsers have timeouts ranging from 40 - 115 sec for sending a close request even when the user has moved away from the current page. This way, the server can service other clients while the current client sends a new request or ends the connection. It was noticed that some browsers would open new connections in parallel + send persistent requests. In this case, this optimization would work perfectly. In the later case, sometime the browser has to wait the whole timeout period for the second connection request to be fulfilled.

	b. Unoptimized: To run this, simply uncomment two lines in the handle() method under MyHandler class. This will allow to check if the 120 s timeout works if the client doesn't reply with any further requests. But the server will block on this client request until the connection is closed; which to me is very wastefull eventhough it is persistent.
	