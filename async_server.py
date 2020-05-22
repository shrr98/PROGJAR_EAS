import socket
import time
import sys
import asyncore
import logging
from http import HttpServer

httpserver = HttpServer()
rcv = ""
Num_Client = None

class ProcessTheClient(asyncore.dispatcher_with_send):
	def handle_read(self):
		global Num_Client, rcv
		data = self.recv(1024)
		if data:
			d = data.decode()
			rcv = rcv + d
			if rcv[-2:] == '\r\n':
				# end of command, proses string
				#logging.warning("data dari client: {}".format(rcv))
				hasil = httpserver.proses(rcv)
				#hasil sudah dalam bentuk bytes
				hasil = hasil + "\r\n\r\n".encode()
				#agar bisa dioperasikan dengan string \r\n\r\n maka harus diencode dulu => bytes

				#nyalakan ketika proses debugging saja, jika sudah berjalan, matikan
				#logging.warning("balas ke  client: {}".format(hasil))
				self.send(hasil) #hasil sudah dalam bentuk bytes, kirimkan balik ke client
				rcv = ""
				self.close()

		# self.send('HTTP/1.1 200 OK \r\n\r\n'.encode())
			#self.send("{}" . format(httpserver.proses(d)))
		self.close()
		Num_Client.value-=1
		logging.warning('CONN CLOSED')


class Server(asyncore.dispatcher):
	def __init__(self, num_client, portnumber):
		asyncore.dispatcher.__init__(self)
		self.num_client = num_client
		self.portnumber = portnumber
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.set_reuse_addr()
		self.bind(('127.0.0.1',portnumber))
		self.listen(50)
		logging.warning("running on port {}" . format(portnumber))

	def handle_accept(self):
		pair = self.accept()
		if pair is not None:
			self.num_client.value += 1
			sock, addr = pair
			logging.warning("connection from {} | {} NUM CLIENT: {}" . format(repr(addr), self.portnumber, self.num_client.value))
			handler = ProcessTheClient(sock)
		logging.warning('APAKAH CLOSED?')

	def handle_close(self):
			self.num_client.value = 0
			logging.warning('{} closed'.format(self.portnumber))

def run_server(num_client, port_number):
	global Num_Client
	logging.warning('CREATING SERVER {}'.format(port_number))
	Num_Client = num_client
	svr = Server(num_client, port_number)
	logging.warning('SERVER CREATED {}'.format(port_number))
	asyncore.loop()