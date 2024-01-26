#!/usr/bin/env python3

import serial
import socket
import time
import sys

s = socket.socket()

s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

port = 42069
s.bind(('127.0.0.1', port))

s.listen(0)

ser = serial.Serial("/dev/ttyUSB3")

ser.write(b'ATE0\r\n')
time.sleep(0.025)
ser.write(b'AT+CMGF=1\r\n')
time.sleep(0.025)
ser.write(b'AT+CNMI=2,2,0,0,0\r\n')
time.sleep(0.025)

def send_sms(num, text):
	ser.write(b'ATZ\r\n')
	time.sleep(0.025)
	ser.write(b'AT+CMGF=1\r\n')
	time.sleep(0.025)
	ser.write(b'AT+CMGS=\"%s\"\r\n' % num.encode())
	time.sleep(0.025)
	ser.write(b'%s\x1a' % text.encode())
	time.sleep(0.025)
	ser.write(b'ATE0\r\n')

def parse_sms(text):
	phone_num = ""
	time = ""
	msg = ""

	# phone num is the first quoted str
	phone_num = text[text.index("\"") + 1:]
	phone_num = phone_num[:phone_num.index("\"")]

	# time is the second after 2 commas
	time = text[text.index(",,\"")+3:]
	time = time[:time.index("\"")]

	# the contents is the next line onwards
	msg = "\n".join(text.split("\r\n")[1:])

	return phone_num, time, msg

while True:
	c, addr = s.accept()

	while True:
		not_empty = True

#		time.sleep(0.025)
		sys.stdout.flush()
		print("a")
		l1 = ser.readline()
		print(l1)

		if not l1.decode().startswith("+CMT:") or l1.decode()[:2] == "OK" or l1.decode() == "\r\n":
			continue
		print("b")
		print(l1)
		print("c")
		s = l1.decode()
		l1 = ser.readline()
		print(l1)
		if l1.decode()[-2:] != "\r\n":
			while not_empty:
				s += l1.decode()
				l1 = ser.readline()
				if l1.decode()[-2:] == "\r\n":
					not_empty = False
		s += l1.decode()
		print("e")

		phone_num, stime, msg = parse_sms(s)

		print("ready")

		c.send(("#%s@%s$%d\"%s\x00" % (phone_num, stime, len(msg), msg)).encode("utf-8"))
		print("sent")

	c.close()

	break
