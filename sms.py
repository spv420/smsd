import weechat
import serial
import socket
import time
import os

weechat.register("sms", "spv", "1.0", "GPL3", "SMS support for weechat", "", "")
ser = serial.Serial(port="/dev/ttyUSB3")
sms_recv_buf = []

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

sock.connect(("127.0.0.1", 42069))
sms_db = []

def db_to_txt(db):
	s = ""

	for v in sms_db:
		s += "%s\x00%s\x00%s\x00%d\x00%s\x01" % (v[0], v[1], v[2], v[3], v[4])

	return s

def txt_to_db(txt):
	db = []
	split_txt = txt.split("\x01")[:-1]

	for v in split_txt:
		split_v = v.split("\x00")
		db.append((split_v[0], split_v[1], split_v[2], int(split_v[3]), split_v[4]))

	return db

def flush_db():
	global sms_db

	txt = db_to_txt(sms_db)

	f = open(weechat.info_get("weechat_config_dir", "") + "/sms.db", "w")
	f.write(txt)
	f.close()

def read_db():
	global sms_db

	f = open(weechat.info_get("weechat_config_dir", "") + "/sms.db", "r")
	txt = f.read()
	f.close()

	sms_db = txt_to_db(txt)

def send_sms(num, text):
	global sms_db

	ser.write(b'ATZ\r\n')
	time.sleep(0.025)

	ser.write(b'AT+CMGF=1\r\n')
	time.sleep(0.025)

	ser.write(b'AT+CMGS=\"%s\"\r\n' % num.encode())
	time.sleep(0.025)

	ser.write(b'%s\x1a' % text.encode())
	time.sleep(1)

	ser.write(b'ATE0\r\n')
	time.sleep(0.025)

	ser.write(b'AT+CNMI=2,2,0,0,0\r\n')

	sms_db.append((num, os.environ["USER"], time.time(), len(text), text))
	flush_db()

# callback for data received in input
def buffer_input_cb(data, buffer, input_data):
	buf_name = weechat.buffer_get_string(buffer, "name")
	send_sms(buf_name, input_data)
	weechat.prnt(buffer, "%s: %s%s" % (os.environ["USER"], weechat.color("green"), input_data))

	return weechat.WEECHAT_RC_OK

# callback called when buffer is closed
def buffer_close_cb(data, buffer):
	flush_db()

	return weechat.WEECHAT_RC_OK

def display_all():
	global sms_db, buffer

	for v in sms_db:
		# check if buffer already exists, if not, create it
		buffer = weechat.buffer_search("python", v[0])

		if buffer == "":
			buffer = weechat.buffer_new(v[0], "buffer_input_cb", "", "buffer_close_cb", "")

		weechat.prnt(buffer, "%s: %s%s" % (v[1], weechat.color("green"), v[4]))

def check_sms_buf(data, remaining_calls):
	global sms_recv_buf, buffer

	for v in sms_recv_buf:
		# check if buffer already exists, if not, create it
		buffer = weechat.buffer_search("python", v[0])

		if buffer == "":
			buffer = weechat.buffer_new(v[0], "buffer_input_cb", "", "buffer_close_cb", "")

		# keep permanent record of the message
		sms_db.append(v)
		flush_db()

		weechat.prnt(buffer, "%s: %s%s" % (v[1], weechat.color("green"), v[4]))

	sms_recv_buf = []

	weechat.hook_timer(1000, 0, 1, "check_sms_buf", "")
	return 0

def check_sms(data):
	s = sock.recv(1024).decode()

	data = s

	return s

def check_sms_cb(data, command, return_code, out, err):
	s = out

	phone_num = s[s.index("#") + 1:s.index("@")]
	sent_time = s[s.index("@") + 1:s.index("$")]
	length = int(s[s.index("$") + 1:s.index("\"")])
	msg = s[s.index("\"") + 1:]

	sms_recv_buf.append((phone_num, phone_num, sent_time, length, msg))
	weechat.hook_process("func:check_sms", 0, "check_sms_cb", "")

	return 0

def sms_command_cb(data, buffer, args):
	blaze_it = args.split(" ")

	if blaze_it[0] == "compose":
		weechat.buffer_new(blaze_it[1], "buffer_input_cb", "", "buffer_close_cb", "")

	return weechat.WEECHAT_RC_OK

if True:
	read_db()
	display_all()
#except:
#	pass

weechat.hook_command("sms", "sms plugin for weechat", "", "", "", "sms_command_cb", "")

weechat.hook_timer(1000, 0, 1, "check_sms_buf", "")
weechat.hook_process("func:check_sms", 0, "check_sms_cb", "")
