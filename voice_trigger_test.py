# coding=UTF-8

from voicecontrol.ttsstt import Conversation
try:
	from config import API_KEY, DEFAULT_LOCALE
	from config import SPHINX_LM, SPHINX_DIC, SPHINX_HMM, SPHINX_TRIGGER
except:
	raise Exception('config.py not found, please copy config.py.example to config.py')

from echo_test import update_status, silence

def main():
	conversation = Conversation(DEFAULT_LOCALE, API_KEY, SPHINX_HMM, SPHINX_LM, SPHINX_DIC, update_status)
	silence(conversation)

	try:
		while 1:
			reply = conversation.listen()
			if reply.find(SPHINX_TRIGGER) < 0:
				continue
			
			if DEFAULT_LOCALE[:2] == 'pt':
				reply = 'Sim?'
			else:
				reply = 'Yes?'

			conversation.say(reply, use_cache = True)

			reply = conversation.listen(use_google = True)
			
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