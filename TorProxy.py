#!/usr/bin/env python
############################################################
## User Settings
############################################################

#Machine running the Tor service. Change address if Tor service isn't running on localhost
TOR_SERVICE_ADDRESS = '127.0.0.1'
#Tor service defaults to post 9050
TOR_SERVICE_PORT = 9050 

#Machine running the TorProxys service. 
#Default will work if usenet tools are all running on this machine, otherwise set this to a local network accessible address.
TORNZBS_SERVICE_ADDRESS = '192.168.0.8'
#TorNZBs service defaults to port 8089. Change if this port is already in use.
TORNZBS_SERVICE_PORT = 8089

#Address of the hidden service to connect to (only one per proxy server)
TORNZBS_HIDDEN_SERVICE = 'nnpbetabzsneptym.onion'

############################################################
## No changes required after this point
############################################################

import SocketServer
import BaseHTTPServer
import SimpleHTTPServer

class ThreadingSimpleServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
	pass

import sys
import socks
import socket
import datetime

orig_sock = socket.socket
socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, TOR_SERVICE_ADDRESS, TOR_SERVICE_PORT)
socket.socket = socks.socksocket

# Proxy DNS Requests
def getaddrinfo(*args):
	return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (args[0], args[1]))]
socket.getaddrinfo = getaddrinfo

import urllib2

def timeStamped(fmt='%Y-%m-%d %H:%M:%S'):
    return datetime.datetime.now().strftime(fmt)

def checkTor():
	try:
		if "Sorry" in urllib2.urlopen('https://check.torproject.org/').read():
			return False
		else:
			return True
	except:
		return False

def checkService():
        try:
                if "TorNZBs" in urllib2.urlopen('http://'+TORNZBS_HIDDEN_SERVICE).read():
                        return True
                else:
                        return False
        except:
                return False


class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def do_GET(s):
		try:
			url = 'http://' + TORNZBS_HIDDEN_SERVICE + s.path
			print (timeStamped() + " - Retrieving URL: %s\r" % (url))
			response = urllib2.urlopen(url)

			s.send_response(response.getcode())
			s.send_header("Content-type", response.info().getheader('Content-Type'))
			if (response.info().getheader('Content-Disposition')):
				s.send_header("Content-Disposition", response.info().getheader('Content-Disposition'))
			s.end_headers()
	
			body = response.read()
			response.close()
			body = body.replace(TORNZBS_HIDDEN_SERVICE, TORNZBS_SERVICE_ADDRESS+':'+str(TORNZBS_SERVICE_PORT))
	
			s.wfile.write(body)
		except socket.error, e:
			print "Socket Error: "+e

if __name__ == '__main__':
	print 'Verifying Tor Connection...'
	if checkTor():
		print 'Tor Connection Verified'

		print 'Checking TorNZBs Connection Status...'
		if checkService():
			print 'TorNZBs Connection Verified.'
		else:
			print 'TorNZBs status could not be verified at this time.'

		print 'Starting TorNZBs Proxy...'
		server = ThreadingSimpleServer(('', TORNZBS_SERVICE_PORT), MyHandler)
		try:
			print 'TorNZBs Proxy Started.'
			while 1:
				sys.stdout.flush()
				server.handle_request()
		except KeyboardInterrupt:
			print "\nStopping TorNZBs Proxy"
	else:
		print 'Error: Tor connection could not be verified.'
