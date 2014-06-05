# coding=UTF-8

from voicecontrol.brain import Brain
from voicecontrol.ttsstt import Conversation
from voicecontrol.ttsstt import STATUS_WAITING, STATUS_LISTENING, STATUS_PROCESSING

try:
	from config import API_KEY, DEFAULT_LOCALE
	from config import SPHINX_LM, SPHINX_DIC, SPHINX_HMM, SPHINX_TRIGGER
	from config import MODULES
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
	conversation = Conversation(DEFAULT_LOCALE, API_KEY, SPHINX_HMM, SPHINX_LM, SPHINX_DIC, update_status)
	brain = Brain(conversation, MODULES)

	print
	print 'Please, allow 2 seconds of silence to calibrate....'
	silence = conversation.calculate_silence(2)
	print "Silence threshold set to:", silence
	print

	try:
		while 1:
			reply = conversation.listen()

			print 'You said:',reply

			if reply.find(SPHINX_TRIGGER) < 0:
				continue
			
			if DEFAULT_LOCALE[:2] == 'pt':
				reply = 'Sim?'
			else:
				reply = 'Yes?'

			print 'Reply:', reply
			conversation.say(reply)

			print
			reply = conversation.listen(use_google = True)
			print 'You said:',reply
			
			if not reply:
				if DEFAULT_LOCALE[:2] == 'pt':
					reply = 'Quê?'
				else:
					reply = 'What?'

			reply = brain.process(reply)
			print
			print 'text to speech...'
			print 'Reply:', reply
			conversation.say(reply)

	except KeyboardInterrupt:
		print
		print 'Bye Bye'

if __name__ == '__main__':
	main()