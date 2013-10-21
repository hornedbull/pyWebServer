# ECEC 433
# Mini-Project (webServer)
# Vatsal Shah

import cgi
import sys
from os import curdir, sep
from BaseHTTPServer import BaseHTTPRequestHandler
from SocketServer import BaseServer
import select
import socket


class MyServer(BaseServer):
    # Subclassed BaseServer class to handle TCP connections
    address_family = socket.AF_INET

    socket_type = socket.SOCK_STREAM
    # Number of requests that can be handled simultaneously by the server
    # using select()
    request_queue_size = 10

    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True):
        # Initialize
        BaseServer.__init__(self, server_address, RequestHandlerClass)
        self.socket = socket.socket(self.address_family,
                                    self.socket_type)
        if bind_and_activate:
            self.server_bind()
            self.server_activate()

    def server_bind(self):
        # Called by constructor to bind the socket
        if self.allow_reuse_address:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)
        self.server_address = self.socket.getsockname()

    def server_activate(self):
        # Called by constructor to start listening
        self.socket.listen(self.request_queue_size)

    def server_close(self):
        # Called to close the server socket
        self.socket.close()

    def fileno(self):
        """Return socket file number.

        Interface required by select().

        """
        return self.socket.fileno()

    def get_request(self):
        # Accept the TCP connection
        return self.socket.accept()

    def shutdown_request(self, request):
        """Called to shutdown and close an individual request."""
        try:
            # explicitly shutdown.  socket.close() merely releases
            # the socket and waits for GC to perform the actual close.
            request.shutdown(socket.SHUT_WR)
        except socket.error:
            pass  # some platforms may raise ENOTCONN here
        self.close_request(request)

    def close_request(self, request):
        """Called to clean up an individual request."""
        request.close()

    def serve_forever(self, poll_interval=0.5):

        try:
            while True:
                # Using select to choose between the requests pending
                r, w, e = select.select([self], [], [], poll_interval)
                if self in r:
                    # Makes a non-blocking call to handle the selected request
                    # The server is still listening for new requests
                    self._handle_request_noblock()
        except KeyboardInterrupt:
            print "#####Force Quit by Server Administrator#####"


class MyHandler(BaseHTTPRequestHandler):
    def parse_request(self):
        """
        The request should be stored in self.raw_requestline; the results
        are in self.command, self.path, self.request_version and
        self.headers.

        Return True for success, False for failure; on failure, an
        error is sent back.

        """
        self.command = None  # set in case of error on the first line
        self.request_version = version = self.default_request_version
        self.close_connection = 1
        requestline = self.raw_requestline
        if requestline[-2:] == '\r\n':
            requestline = requestline[:-2]
        elif requestline[-1:] == '\n':
            requestline = requestline[:-1]
        self.requestline = requestline
        words = requestline.split()
        if len(words) == 3:
            [command, path, version] = words
            if version[:5] != 'HTTP/':
                self.send_error(400, "Bad request version (%r)" % version)
                return False
            try:
                base_version_number = version.split('/', 1)[1]
                version_number = base_version_number.split(".")
                # RFC 2145 section 3.1 says there can be only one "." and
                #   - major and minor numbers MUST be treated as
                #      separate integers;
                #   - Leading zeros MUST be ignored by recipients.
                if len(version_number) != 2:
                    raise ValueError
                version_number = int(version_number[0]), int(version_number[1])
            except (ValueError, IndexError):
                self.send_error(400, "Bad request version (%r)" % version)
                return False
            if version_number >= (1, 1) and self.protocol_version >= "HTTP/1.1":
                # Persistent Connection - Keeps connection alive for subsequent
                # requests
                self.close_connection = 0
            if version_number >= (2, 0):
                self.send_error(505,
                                "Invalid HTTP Version (%s)" % base_version_number)
                return False
        elif len(words) == 2:
            [command, path] = words
            self.close_connection = 1
            if command != 'GET':
                self.send_error(400,
                                "Bad HTTP/0.9 request type (%r)" % command)
                return False
        elif not words:
            return False
        else:
            self.send_error(400, "Bad request syntax (%r)" % requestline)
            return False
        self.command, self.path, self.request_version = command, path, version

        # Examine the headers and look for a Connection directive
        self.headers = self.MessageClass(self.rfile, 0)

        conntype = self.headers.get('Connection', "")
        # Closes the connection if client header Connection: close
        # If Connection: keep-alive, server doesn't close the socket
        if conntype.lower() == 'close':
            self.close_connection = 1
        elif (conntype.lower() == 'keep-alive' and
              self.protocol_version >= "HTTP/1.1"):
            self.close_connection = 0
        return True

    def handle_one_request(self):
        # Waits 120 s for read/write operation by a connection. Otherwise
        # closes it
        socket.setdefaulttimeout(120)
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(414)
                return
            if not self.raw_requestline:
                self.close_connection = 1
                return
            if not self.parse_request():
                # An error code has been sent, just exit
                return
            mname = 'do_' + self.command
            if not hasattr(self, mname):
                self.send_error(501, "Unsupported method (%r)" % self.command)
                return
            method = getattr(self, mname)
            method()
            self.wfile.flush(
            )  # actually send the response if not already done.
        except socket.timeout, e:
            # a read or a write timed out.  Discard this connection
            self.log_error("Request timed out: %r", e)
            self.close_connection = 1
            return

    def handle(self):
        self.close_connection = 1
        # Handles the client requests sent by select in serve_forever()
        # Only closes the connection if client requested close or request times
        # out (120s)
        self.handle_one_request()
        """
        Uncomment the following code to check for persistent connection and 120s timeout handling.
        This would make the handler wait until all the requests from a particular client socket are
        handled before moving on to the next one. For optimization, this has been commented out. This
        allows the handler to move on to the next request while waiting for a particular client to
        respond. Though it moves on, it maintains the connection with the client until a Connection: close
        request is received or the read/write times out.

        """
#        while not self.close_connection:
#            self.handle_one_request()

    # Handles GET command
    def do_GET(self):
        try:
            if self.path.endswith(".html"):
                # Calculates the path and saves it to a fileObject
                f = open(curdir + sep + self.path)
                content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                # Content-Length required by HTTP1.1 for html pages
                self.send_header('Content-Length', len(content))
                self.end_headers()
                self.wfile.write(content)
                f.close()
                return
            if self.path.endswith(".jpg"):  # image files
                f = open(curdir + sep + self.path, 'rb')
                content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'image/jpeg')
                self.end_headers()
                self.wfile.write(content)
                f.close()
                return
            if self.path.endswith(".png"):  # image files
                f = open(curdir + sep + self.path)
                content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'image/png')
                self.end_headers()
                self.end_headers()
                self.wfile.write(content)
                f.close()
                return
            if self.path.endswith(".pdf"):  # image files
                f = open(curdir + sep + self.path, 'rb')
                content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'application/pdf')
                self.end_headers()
                self.wfile.write(content)
                f.close()
                return

            return

        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)

    # Handles POST command
    def do_POST(self):
        global rootnode
        try:
            ctype, pdict = cgi.parse_header(
                self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                query = cgi.parse_multipart(self.rfile, pdict)
            self.send_response(301)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            upfilecontent = query.get('upfile')
            print "POST Request file content: \n", upfilecontent[0]
            self.wfile.write(upfilecontent[0])

        except:
            pass

# Calls the Server and the handler class
# The protocol version decides HTTP persistent/non-persistent connections
# HTTP1.1 = Persistent, HTTP1.0 = Non-Persistent
# The handler class differentiates between the two protocols and how it
# handles a request


def test(HandlerClass=MyHandler, ServerClass=MyServer, protocol="HTTP/1.1"):
    # Command-line argument can be passed to change the port
    if sys.argv[1:]:
        port = int(sys.argv[1])
    else:
        port = 22222
    server_address = ('127.0.0.1', port)

    HandlerClass.protocol_version = protocol
    httpd = ServerClass(server_address, HandlerClass)

    sa = httpd.socket.getsockname()
    print "Serving HTTP on", sa[0], "port", sa[1], "..."
    httpd.serve_forever()


if __name__ == '__main__':
    test()
