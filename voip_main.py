#!/usr/bin/env python
# coding=UTF-8

import sys
import pjsua as pj
import time
import wave
import threading
import math

from voicecontrol.brain import Brain
from voicecontrol.ttsstt import Conversation
from voicecontrol.ttsstt import STATUS_WAITING, STATUS_LISTENING, STATUS_PROCESSING, STATUS_LISTENED, STATUS_SAID

try:
	from config import PJSIP_USERNAME, PJSIP_PASSWORD, PJSIP_REGISTAR, PJSIP_PROXY, PJSIP_ID
	from config import API_KEY, DEFAULT_LOCALE
	from config import MODULES
except:
	raise Exception('config.py not found, please copy config.py.example to config.py')

current_call = None
brain = None
LOG_LEVEL=1

#########################
# yeah, TODO: use gettext

conversation = None

I18N_DATA = {
	'pt-PT': {
		'Yes?': 'Sim?',
		'What?': 'Quê?',
		'Hello': 'Olá',
		'One moment': 'Um momento',
		'Hello. Press any key to start talking and press any key again once you are done': 'Olá. Pressiona qualquer tecla para começar a falar e volta a pressionar quando acabares.',
	},
}

def _(text):
	if conversation:
		if conversation.lang_code in I18N_DATA:
			lang = conversation.lang_code
			text = I18N_DATA[lang].get(text, text)
	return text
#########################

class HelloThread(threading.Thread):
	def __init__(self, t, *args):
		self._real_target = t
		threading.Thread.__init__(self, target=self._delay, args=args)
		self._cancel = threading.Event()
		self.start()

	def _delay(self, *args):
		pj.Lib.instance().thread_register('delaysay')
		time.sleep(2)
		if not self._cancel.isSet():
			self._real_target(args[0])

	def cancel(self):
		self._cancel.set()

class BrainThread(threading.Thread):
	def __init__(self, brain):
		threading.Thread.__init__(self, target=self.main)
		self._brain = brain
		self._stop = threading.Event()
		self.start()

	def main(self):
		pj.Lib.instance().thread_register('braindead')
		while not self._stop.isSet():
			input = self._brain.conversation.listen()
			if self._stop.isSet():
				break
			if input:
				(done, reply) = self._brain.process(input)

				if not done:
					self._brain.conversation.say(_('What?'), use_cache = True)
				elif reply:
					self._brain.conversation.say(reply)

			else:
				self._brain.conversation.say(_('What?'), use_cache = True)

	def stop(self):
		self._stop.set()
		self._brain.conversation.listen_shutdown()


class ConversationVOIP(Conversation):
	def __init__(self, lang_code, api_key, sphinx_hmm = None, sphinx_lm = None, sphinx_dic = None, callback = None):
		# ignore sphinx options
		super(ConversationVOIP, self).__init__(lang_code, api_key, None, None, None, callback)
		self.sttfile = self._stt._wavfile
		# set rate to 16000
		self._stt.RATE = 16000
		self.call = None
		self._player = None
		self._recorder = None
		self._listen_start_lock = threading.Lock()
		self._listen_stop_lock = threading.Lock()
		self._listening = False
		self._shutdown = False
	
	def listen(self, use_google = False):
		# always use_google

		if not self.call:
			return

		# lock the locks (to be released by listen_start and listen_stop)
		self._listen_stop_lock.acquire()
		if not self._listening: # dont pre-lock if already listening
			self._listen_start_lock.acquire()

		# again, now it will hang...
		with self._listen_start_lock:
			if self._shutdown : return None

			call_slot = self.call.info().conf_slot
			lib = pj.Lib.instance()

			self._recorder = lib.create_recorder(self.sttfile)
			recorder_slot = lib.recorder_get_slot(self._recorder)
			lib.conf_connect(call_slot, recorder_slot)
		
			with self._listen_stop_lock:
				if self._shutdown : return None

				self.say(_('One moment'), use_cache = True)

				lib.conf_disconnect(recorder_slot, call_slot)
				lib.recorder_destroy(self._recorder)
				self._recorder = None

				val = self._stt.stt_google(self.sttfile)
				self._stt.notify_status(STATUS_LISTENED, val)
				return val

	def listen_start(self, use_google = False):
		self._listening = True
		try:
			self._listen_start_lock.release()
		except:
			print 'start not locked!!!'

	def listen_stop(self, use_google = False):
		self._listening = False
		try:
			self._listen_stop_lock.release()
		except:
			print 'stop not locked!!!'

	def listen_shutdown(self):
		self._shutdown = True
		try:
			self._listen_stop_lock.release()
		except:
			pass
		try:
			self._listen_start_lock.release()
		except:
			pass

	def listen_reset(self):
		self.call = None
		self._player = None
		self._recorder = None
		self._listening = False
		self._shutdown = False

	def say(self, text, use_cache = False):
		if not self.call:
			return

		self._stt.notify_status(STATUS_SAID, text)
		filename = self._tts.text_to_audio_file(text, use_cache, convert_to_wav = True)

		if self._listening or self._shutdown:
			return

		call_slot = self.call.info().conf_slot
		lib = pj.Lib.instance()

		if self._player != None:
			player_slot = lib.player_get_slot(self._player)
			lib.conf_disconnect(player_slot, call_slot)
			lib.player_destroy(self._player)
			self._player = None

		f = wave.open(filename,'r')
		frames = f.getnframes()
		rate = f.getframerate()
		duration = frames / float(rate)
		f.close()
		self._player = lib.create_player(filename)
		player_slot = lib.player_get_slot(self._player)
		lib.conf_connect(player_slot, call_slot)
		# split into blocks of 0.2s
		sleep_blocks = int(math.ceil(duration / 0.2))
		for i in xrange(sleep_blocks):
			if self._listening or self._shutdown:
				break
			time.sleep(0.2)

		if (self._player != None) and (not self._shutdown):
			player_slot = lib.player_get_slot(self._player)
			lib.conf_disconnect(player_slot, call_slot)
			lib.player_destroy(self._player)
			self._player = None

	def calculate_silence(self, seconds = 5):
		return 0

# Callback to receive events from Call
class MyCallCallback(pj.CallCallback):

	def __init__(self, call=None):
		pj.CallCallback.__init__(self, call)
		self._state = 0
		self._player = None
		self._recorder = None
		self._last_said = None
		self._hello_thread = None
		self._brain_thread = None

	# Notification when call state has changed
	def on_state(self):
		global current_call
		print "Call with", self.call.info().remote_uri,
		print "is", self.call.info().state_text,
		print "last code =", self.call.info().last_code, 
		print "(" + self.call.info().last_reason + ")"
		
		if self.call.info().state == pj.CallState.DISCONNECTED:
			current_call = None
			if self._hello_thread:
				self._hello_thread.cancel()
			if self._brain_thread:
				self._brain_thread.stop()
			conversation.call = current_call
			print 'Current call is', current_call

	# Notification when call's media state has changed.
	def on_media_state(self):
		if self.call.info().media_state == pj.MediaState.ACTIVE:
			self._hello_thread = HelloThread(conversation.say, _('Hello. Press any key to start talking and press any key again once you are done'))
			self._brain_thread = BrainThread(brain)

	def on_dtmf_digit(self, digits):
		# any digit triggers this
		print 'State:', self._state, ' (', digits, ')'

		call_slot = self.call.info().conf_slot
		lib = pj.Lib.instance()

		if self._hello_thread:
			self._hello_thread.cancel()

		if self._state == 0:
			conversation.listen_start()
		elif self._state == 1:
			conversation.listen_stop()
			
		self._state = (self._state + 1) % 2
		

# Callback to receive events from account
class MyAccountCallback(pj.AccountCallback):

	def __init__(self, account=None):
		pj.AccountCallback.__init__(self, account)

	# Notification on incoming call
	def on_incoming_call(self, call):
		global current_call 
		if current_call:
			call.answer(486, "Busy")
			return
			
		print "Incoming call from ", call.info().remote_uri

		current_call = call
		conversation.listen_reset()
		conversation.call = current_call

		call_cb = MyCallCallback(current_call)
		current_call.set_callback(call_cb)

		current_call.answer(200)

def main():
	# Create library instance
	lib = pj.Lib()

	try:
		lib.init(log_cfg = pj.LogConfig(level=LOG_LEVEL, callback=log_cb))
		lib.set_null_snd_dev()

		transport = lib.create_transport(pj.TransportType.UDP, 
										 pj.TransportConfig(0))

		print "\nListening on", transport.info().host, 
		print "port", transport.info().port, "\n"
		
		lib.start()

		acc_cfg = pj.AccountConfig()
		acc_cfg.id = 'sip:' + PJSIP_ID
		acc_cfg.reg_uri = 'sip:' + PJSIP_REGISTAR
		acc_cfg.proxy = [ 'sip:' + PJSIP_PROXY ]
		acc_cfg.auth_cred = [ pj.AuthCred("*", PJSIP_USERNAME, PJSIP_PASSWORD) ]

		acc = lib.create_account(acc_cfg, cb=MyAccountCallback())

		#my_sip_uri = "sip:" + transport.info().host + ":" + str(transport.info().port)

		global conversation, brain
		conversation = ConversationVOIP(DEFAULT_LOCALE, API_KEY, callback = update_status)
		brain = Brain(conversation, MODULES)

		print 'Modules loaded:'
		for m in brain.modules:
			print m.__name__

		# Menu loop
		while True:
			print
			print "My SIP URI is", acc_cfg.id
			print "Menu:  h=hangup call, q=quit"

			input = sys.stdin.readline().rstrip("\r\n")

			if input == "h":
				if not current_call:
					print "There is no call"
					continue
				current_call.hangup()

			elif input == "q":
				if current_call : current_call.hangup()
				break

		transport = None
		acc.delete()
		acc = None
		lib.destroy()
		lib = None

	except pj.Error, e:
		print "Exception: " + str(e)
		lib.destroy()
		lib = None

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

def log_cb(level, str, len):
	if level <= LOG_LEVEL:
		print level, str,

if __name__ == '__main__':
	main()