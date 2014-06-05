# coding=UTF-8

from voicecontrol.ttsstt import Conversation
from voicecontrol.ttsstt import STATUS_WAITING, STATUS_LISTENING, STATUS_PROCESSING, STATUS_LISTENED, STATUS_SAID
try:
	from config import API_KEY, DEFAULT_LOCALE
except:
	raise Exception('config.py not found, please copy config.py.example to config.py')

def update_status(status, value = None):
	if status == STATUS_WAITING:
		print
		print "please speak into the microphone"
	elif status == STATUS_LISTENING:
		print "Listening..."
	elif status == STATUS_PROCESSING:
		print "speech to text..."
	elif status == STATUS_LISTENED:
		print "You said:", value
	elif status == STATUS_SAID:
		print "I said:", value

def silence(conversation, seconds = 2):
	print
	print 'Please, allow %d seconds of silence to calibrate....' % seconds
	silence = conversation.calculate_silence(seconds)
	print "Silence threshold set to:", silence
	print

def main():
	conversation = Conversation(DEFAULT_LOCALE, API_KEY, callback = update_status)
	silence(conversation)

	try:
		while 1:
			reply = conversation.listen()

			if not reply:
				if DEFAULT_LOCALE[:2] == 'pt':
					reply = 'Quê?'
				else:
					reply = 'What?'
				conversation.say(reply, use_cache = True)
			else:
				conversation.say(reply)
	except KeyboardInterrupt:
		print
		print 'Bye Bye'

if __name__ == '__main__':
	main()