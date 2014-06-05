# coding=UTF-8

from voicecontrol.ttsstt import Conversation
from voicecontrol.ttsstt import STATUS_WAITING, STATUS_LISTENING, STATUS_PROCESSING
try:
	from config import API_KEY, DEFAULT_LOCALE
except:
	raise Exception('config.py not found, please copy config.py.example to config.py')


def update_status(status):
	if status == STATUS_WAITING:
		print "please speak into the microphone"
	elif status == STATUS_LISTENING:
		print "Listening..."
	elif status == STATUS_PROCESSING:
		print "speech to text..."

def main():
	conversation = Conversation(DEFAULT_LOCALE, API_KEY, callback = update_status)
	print 'Please, allow 5 seconds of silence to calibrate....'
	silence = conversation.calculate_silence(5)
	print "Silence threshold set to:", silence
	print
	try:
		while 1:
			reply = conversation.listen()

			if not reply:
				if DEFAULT_LOCALE[:2] == 'pt':
					reply = 'Não percebi, repete por favor.'
				else:
					reply = 'I did not understand, please repeat.'
			print
			print 'text to speech...'
			print 'Reply:', reply
			conversation.say(reply)
	except KeyboardInterrupt:
		print
		print 'Bye Bye'

if __name__ == '__main__':
	main()