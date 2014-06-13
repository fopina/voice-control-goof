# coding=UTF-8

import sys
import pjsua as pj
import time
import wave

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

def log_cb(level, str, len):
	if level <= LOG_LEVEL:
		print level, str,

class ConversationVOIP(Conversation):
	def __init__(self, lang_code, api_key, sphinx_hmm = None, sphinx_lm = None, sphinx_dic = None, callback = None):
		# ignore sphinx options
		super(ConversationVOIP, self).__init__(lang_code, api_key, None, None, None, callback)
		self.sttfile = self._stt._wavfile
		# set rate to 16000
		self._stt.RATE = 16000
		self.call = None
		self._player = None
	
	def listen(self, use_google = False):
		if not self.call:
			return None
		# always use_google
		val = self._stt.stt_google(self.sttfile, convert_to_flac = False)
		self._stt.notify_status(STATUS_LISTENED, val)
		return val

	def say(self, text, use_cache = False):
		if not self.call:
			return

		self._stt.notify_status(STATUS_SAID, text)
		filename = self._tts.text_to_audio_file(text, use_cache, convert_to_wav = True)

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
		time.sleep(duration)

	def calculate_silence(self, seconds = 5):
		return 0

# Callback to receive events from Call
class MyCallCallback(pj.CallCallback):

	def __init__(self, call=None):
		pj.CallCallback.__init__(self, call)
		self._state = -1
		self._player = None
		self._recorder = None
		self._last_said = None

	# Notification when call state has changed
	def on_state(self):
		global current_call
		print "Call with", self.call.info().remote_uri,
		print "is", self.call.info().state_text,
		print "last code =", self.call.info().last_code, 
		print "(" + self.call.info().last_reason + ")"
		
		if self.call.info().state == pj.CallState.DISCONNECTED:
			current_call = None
			conversation.call = current_call
			print 'Current call is', current_call

	# Notification when call's media state has changed.
	def on_media_state(self):
		if self.call.info().media_state == pj.MediaState.ACTIVE:
			call_slot = self.call.info().conf_slot
			# it seems that if no conf_connect is called, it hangs
			pj.Lib.instance().conf_connect(call_slot, 0)

	def on_dtmf_digit(self, digits):
		# any digit triggers this
		call_slot = self.call.info().conf_slot
		lib = pj.Lib.instance()

		if self._recorder != None:
			recorder_slot = lib.recorder_get_slot(self._recorder)
			lib.conf_disconnect(recorder_slot, call_slot)
			lib.recorder_destroy(self._recorder)
			self._recorder = None
			self._last_said = conversation.listen()


		if self._state == 0:
			if self._last_said:
				reply = brain.process(self._last_said)

				if reply:
					conversation.say(reply)

				self._last_said = None
			else:
				conversation.say(_('Hello'), use_cache = True)
			
		elif self._state == 1:
			self._recorder = lib.create_recorder(conversation.sttfile)
			recorder_slot = lib.recorder_get_slot(self._recorder)
			lib.conf_connect(call_slot, recorder_slot)

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
		conversation.call = current_call

		call_cb = MyCallCallback(current_call)
		current_call.set_callback(call_cb)

		current_call.answer(200)

def main():
	# Create library instance
	lib = pj.Lib()

	try:
		lib.init(log_cfg = pj.LogConfig(level=LOG_LEVEL, callback=log_cb))

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

		my_sip_uri = "sip:" + transport.info().host + ":" + str(transport.info().port)


		global conversation, brain
		conversation = ConversationVOIP(DEFAULT_LOCALE, API_KEY, callback = update_status)
		brain = Brain(conversation, MODULES)

		print 'Modules loaded:'
		for m in brain.modules:
			print m.__name__

		# Menu loop
		while True:
			print
			print "My SIP URI is", my_sip_uri
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

if __name__ == '__main__':
	main()