#!/usr/bin/env python
# coding=UTF-8

from voicecontrol.ttsstt import Conversation
try:
	from config import API_KEY, DEFAULT_LOCALE
	from config import SPHINX_LM, SPHINX_DIC, SPHINX_HMM, SPHINX_TRIGGER
	from config import MP3_PLAY, OFFLINETTS
except:
	raise Exception('config.py not found, please copy config.py.example to config.py')

from echo_test import update_status, silence
from main import _
import main as mm

def main():
	conversation = Conversation(DEFAULT_LOCALE, API_KEY, SPHINX_HMM, SPHINX_LM, SPHINX_DIC, update_status, mp3player = MP3_PLAY, offline_tts = OFFLINETTS)
	mm.conversation = conversation
	silence(conversation)

	try:
		while 1:
			reply = conversation.listen()
			if reply.find(SPHINX_TRIGGER) < 0:
				continue
			
			conversation.say(_('Yes?'), use_cache = True)
			reply = conversation.listen(use_google = True)
			
			if not reply:
				conversation.say(_('What?'), use_cache = True)
			else:
				conversation.say(reply)

	except KeyboardInterrupt:
		print
		print 'Bye Bye'

if __name__ == '__main__':
	main()