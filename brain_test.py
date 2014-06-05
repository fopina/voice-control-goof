# coding=UTF-8

from voicecontrol.brain import Brain
from voicecontrol.ttsstt import ConversationWithoutAudio
import sys

try:
	from config import DEFAULT_LOCALE
	from config import SPHINX_LM, SPHINX_DIC, SPHINX_HMM, SPHINX_TRIGGER
	from config import MODULES
except:
	raise Exception('config.py not found, please copy config.py.example to config.py')

def main():
	conversation = ConversationWithoutAudio(DEFAULT_LOCALE, '')
	brain = Brain(conversation, MODULES)

	print 'Modules loaded:'
	for m in brain.modules:
		print m.__name__

	print
	print 'Input: ',
	if len(sys.argv) > 1:
		input = ' '.join(sys.argv[1:])
		print input
	else:
		input = conversation.listen()
	output = conversation.say(brain.process(input))
	print 'Output:',
	if output:
		print output
	else:
		print '(none)'

if __name__ == '__main__':
	main()