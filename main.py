# coding=UTF-8

from voicecontrol.brain import Brain
from voicecontrol.ttsstt import Conversation
from voicecontrol.ttsstt import STATUS_WAITING, STATUS_LISTENING, STATUS_PROCESSING, STATUS_LISTENED, STATUS_SAID

try:
	from config import API_KEY, DEFAULT_LOCALE
	from config import SPHINX_LM, SPHINX_DIC, SPHINX_HMM, SPHINX_TRIGGER
	from config import MODULES
except:
	raise Exception('config.py not found, please copy config.py.example to config.py')


#########################
# yeah, TODO: use gettext

conversation = None
I18N_DATA = {
	'pt-PT': {
		'Yes?': 'Sim?',
		'What?': 'Quê?',
	},
}

def _(text):
	if conversation:
		if conversation.lang_code in I18N_DATA:
			lang = conversation.lang_code
			text = I18N_DATA[lang].get(text, text)
	return text
#########################


def update_status(status, value = None):
	if status == STATUS_WAITING:
		print "please speak into the microphone"
	elif status == STATUS_LISTENING:
		print "Listening..."
	elif status == STATUS_PROCESSING:
		print "speech to text..."
	elif status == STATUS_LISTENED:
		print "You said:", value
	elif status == STATUS_SAID:
		print "I said:", value

def main():
	global conversation
	conversation = Conversation(DEFAULT_LOCALE, API_KEY, SPHINX_HMM, SPHINX_LM, SPHINX_DIC, update_status)
	brain = Brain(conversation, MODULES)

	print 'Modules loaded:'
	for m in brain.modules:
		print m.__name__

	print
	print 'Please, allow 2 seconds of silence to calibrate....'
	silence = conversation.calculate_silence(2)
	print "Silence threshold set to:", silence
	print

	try:
		while 1:
			reply = conversation.listen()

			if reply.find(SPHINX_TRIGGER) < 0:
				continue
			
			conversation.say(_('Yes?'), use_cache = True)

			print
			reply = conversation.listen(use_google = True)
			
			if not reply:
				conversation.say(_('What?'), use_cache = True)
				continue

			reply = brain.process(reply)

			if reply:
				conversation.say(reply)

	except KeyboardInterrupt:
		print
		print 'Bye Bye'

if __name__ == '__main__':
	main()