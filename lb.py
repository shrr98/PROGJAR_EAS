import socket
import time
import sys
import asyncore
import logging
import multiprocessing as mp
from async_server import run_server

class BackendList:
	MAX_CLIENT = 20

	def __init__(self):
		self.servers=[]
		self.server_process = []
		self.num_client = []
		self.port = 9002
		self.add_server()

	def add_server(self):
		num_client = mp.Value('i')
		num_client.value = 0
		self.num_client.append(num_client)

		proses = mp.Process(target=run_server, args=(num_client, self.port))
		proses.start()
		self.server_process.append(proses)

		self.servers.append(('127.0.0.1', self.port))
		self.port += 1

	def getserver(self):
		is_ready = True
		current = self.get_current()
		if current<0:
			logging.warning('TAMBAH WORKER LUR')
			current = len(self.servers)
			self.add_server()
			is_ready = False
		s = self.servers[current]
		return (is_ready, s)

	def get_current(self):
		index = -1
		for i, num_client in enumerate(self.num_client):
			with num_client.get_lock():
				if num_client.value < self.MAX_CLIENT:
					index = i
					break
		return index


class Backend(asyncore.dispatcher_with_send):
	def __init__(self,targetaddress):
		asyncore.dispatcher_with_send.__init__(self)
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connect(targetaddress)
		self.connection = self

	def handle_read(self):
		try:
			self.client_socket.send(self.recv(8192))
		except:

			pass
	def handle_close(self):
		try:
			self.close()
			self.client_socket.close()
		except:
			pass


class ProcessTheClient(asyncore.dispatcher):
	def handle_read(self):
		data = self.recv(8192)
		if data:
			self.backend.client_socket = self
			self.backend.send(data)
	def handle_close(self):
		self.close()

class Server(asyncore.dispatcher):
	def __init__(self,portnumber):
		asyncore.dispatcher.__init__(self)
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.set_reuse_addr()
		self.bind(('',portnumber))
		self.received_req = 0
		self.listen(50)
		self.bservers = BackendList()
		logging.warning("load balancer running on port {}" . format(portnumber))

	def handle_accept(self):
		self.received_req += 1
		logging.warning('RECEIVED REQ : {}'.format(self.received_req))
		pair = self.accept()
		if pair is not None:
			sock, addr = pair
			logging.warning("connection from {}" . format(repr(addr)))

			#menentukan ke server mana request akan diteruskan
			ret, bs = self.bservers.getserver()
			logging.warning("koneksi dari {} diteruskan ke {}" . format(addr, bs))
			if not ret:
				while not isOpen(bs):
					logging.warning('{} not ready'.format(bs))
					time.sleep(.5)
			backend = Backend(bs)

			#mendapatkan handler dan socket dari client
			handler = ProcessTheClient(sock)
			handler.backend = backend

def isOpen(addr):
   s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   try:
      s.connect(addr)
      s.shutdown(2)
      return True
   except:
      return False

def main():
	portnumber=44444
	try:
		portnumber=int(sys.argv[1])
	except:
		pass
	svr = Server(portnumber)
	asyncore.loop()

if __name__=="__main__":
	main()


