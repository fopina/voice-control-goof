# coding=UTF-8

from sys import byteorder
from array import array
from struct import pack

import pyaudio
import wave
import os
import urllib,urllib2
import json
import sys
import tempfile

# stupid bug
try:
	import pocketsphinx
except:
	import pocketsphinx

# Reference for API:
# https://github.com/gillesdemey/google-speech-v2

# callback status
STATUS_WAITING = 1
STATUS_LISTENING = 2
STATUS_PROCESSING = 3
STATUS_LISTENED = 4
STATUS_SAID = 5


# binaries to help
SOX_CONV = 'sox %s -b 16 %s rate 16k'
FLAC_CONV = 'flac -f'  # We need a WAV to FLAC converter. flac is available
					   # on Linux

class STT(object):
	# google speech v2 api endpoint
	GOOGLE_SPEECH_URL = 'https://www.google.com/speech-api/v2/recognize?output=json&lang=%s&key=%s'

	# pyaudio record settings
	THRESHOLD = 500
	CHUNK_SIZE = 1024
	FORMAT = pyaudio.paInt16
	RATE = 44100
	SILENCE_STOP = 20

	def __init__(self, lang_code, api_key, sphinx_hmm = None, sphinx_lm = None, sphinx_dic = None, callback = None):
		self.lang_code = lang_code  # Language to use
		self.api_key = api_key
		self.statuscb = callback

		fd, wavfile = tempfile.mkstemp(suffix = '.wav')
		os.close(fd)
		self._wavfile = wavfile
		self._flacfile = wavfile + '.flac'
		self._ratefile = wavfile + '.16k.wav'

		if sphinx_lm and sphinx_hmm and sphinx_dic:
			self.sphinx_rec = pocketsphinx.Decoder(hmm=sphinx_hmm, lm=sphinx_lm, dict=sphinx_dic, logfn = '/dev/null')
		else:
			self.sphinx_rec = None

	def calculate_silence(self, seconds = 10):
			p = pyaudio.PyAudio()
			stream = p.open(format=self.FORMAT,
				channels=1,
				rate=self.RATE,
				input=True,
				frames_per_buffer=self.CHUNK_SIZE)

			r = array('h')

			maxes = []
			for i in xrange(int(self.RATE/self.CHUNK_SIZE * seconds)):
				snd_data = array('h', stream.read(self.CHUNK_SIZE))
				if byteorder == 'big':
					snd_data.byteswap()
				r.extend(snd_data)
				maxes.append(max(snd_data))

			stream.stop_stream()
			stream.close()
			p.terminate()

			self.THRESHOLD = max(maxes)
			return self.THRESHOLD

	def record(self, trim = True, normalize = True, pad_silence = 0.0):
		"""
		Record audio from the microphone and
		return the data as an array of signed shorts.

		Optionally:
		Normalizes the audio, trims silence from the 
		start and end, and pads with 0.5 seconds of 
		blank sound to make sure VLC et al can play 
		it without getting chopped off.
		"""
		def _is_silent(snd_data, threshold):
			"Returns 'True' if below the 'silent' threshold"
			return max(snd_data) < threshold

		def _normalize(snd_data):
			"Average the volume out"
			MAXIMUM = 16384
			times = float(MAXIMUM)/max(abs(i) for i in snd_data)

			r = array('h')
			for i in snd_data:
				r.append(int(i*times))
			return r

		def _trim(snd_data, threshold):
			"Trim the blank spots at the start and end"
			def __trim(snd_data):
				snd_started = False
				r = array('h')

				for i in snd_data:
					if not snd_started and abs(i)>threshold:
						snd_started = True
						r.append(i)

					elif snd_started:
						r.append(i)
				return r

			# Trim to the left
			snd_data = __trim(snd_data)

			# Trim to the right
			snd_data.reverse()
			snd_data = __trim(snd_data)
			snd_data.reverse()
			return snd_data

		def _add_silence(snd_data, seconds, rate):
			"Add silence to the start and end of 'snd_data' of length 'seconds' (float)"
			r = array('h', [0 for i in xrange(int(seconds*rate))])
			r.extend(snd_data)
			r.extend([0 for i in xrange(int(seconds*rate))])
			return r
		
		p = pyaudio.PyAudio()
		stream = p.open(format=self.FORMAT,
			channels=1,
			rate=self.RATE,
			input=True,
			frames_per_buffer=self.CHUNK_SIZE)

		num_silent = 0
		snd_started = False

		r = array('h')

		while 1:
			# little endian, signed short
			snd_data = array('h', stream.read(self.CHUNK_SIZE))
			if byteorder == 'big':
				snd_data.byteswap()
			r.extend(snd_data)

			silent = _is_silent(snd_data, self.THRESHOLD)

			if snd_started:
				if silent:
					num_silent += 1
				else:
					num_silent = 0
			else:
				if not silent:
					self.notify_status(STATUS_LISTENING)
					snd_started = True

			if snd_started and num_silent > self.SILENCE_STOP:
				break

		sample_width = p.get_sample_size(self.FORMAT)
		stream.stop_stream()
		stream.close()
		p.terminate()

		if normalize : r = _normalize(r)
		if trim : r = _trim(r, self.THRESHOLD)
		if pad_silence : r = _add_silence(r, pad_silence, self.RATE)
		return sample_width, r

	def record_to_file(self,path):
		"""
		Records from the microphone and outputs the resulting data to 'path'
		"""
		sample_width, data = self.record()
		data = pack('<' + ('h'*len(data)), *data)

		wf = wave.open(path, 'wb')
		wf.setnchannels(1)
		wf.setsampwidth(sample_width)
		wf.setframerate(self.RATE)
		wf.writeframes(data)
		wf.close()

	def stt_google(self, audio_fname, convert_to_flac = True):
		"""
		Sends audio file (audio_fname) to Google's text to speech 
		service and returns service's response.
		FLAC converter is required because audio is not FLAC
		(configure FLAC_CONV).
		"""
		def _choose_guess(guesses):
			winner = None
			maxconf = -1
			for guess in guesses:
				conf = float(guess.get('confidence',0))
				if conf > maxconf:
					winner = guess['transcript']
					maxconf = conf
			if winner : winner = winner.encode('utf-8')
			return winner

		if convert_to_flac:
			if os.system('%s -o %s %s 2>/dev/null' % (FLAC_CONV, self._flacfile, audio_fname)):
				raise Exception('%s -o %s %s 2>/dev/null' % (FLAC_CONV, self._flacfile, audio_fname))
			filename = self._flacfile
		else:
			filename = audio_fname

		f = open(filename, 'rb')
		flac_cont = f.read()
		f.close()

		# Headers. A common Chromium (Linux) User-Agent
		hrs = {}
		hrs['User-Agent'] = 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.63 Safari/535.7'
		if convert_to_flac:
			hrs['Content-type'] = 'audio/x-flac; rate=%s' % self.RATE
		else:
			hrs['Content-type'] = 'audio/l16; rate=%s' % self.RATE

		req = urllib2.Request(self.GOOGLE_SPEECH_URL %  (self.lang_code, self.api_key), data=flac_cont, headers=hrs)
		
		try:
			p = urllib2.urlopen(req)
			# what's with the multiple json response?
			responses = p.read().split('\n')
			alts = []
			for response in responses:
				if response:
					res = json.loads(response)
					if res.get('result_index') != None:
						for re in res['result'][res['result_index']]['alternative']:
							alts.append(re)
			res = alts
		except KeyboardInterrupt:
			raise            
		except:
			print "Couldn't parse service response"
			print "Unexpected error:", sys.exc_info()[0]
			res = None

		return _choose_guess(res)

	def stt_sphinx(self, filename):
		if not self.sphinx_rec:
			raise Exception('pocketsphinx not initialized')

		if self.RATE not in (8000,16000):
			if os.system(SOX_CONV % (filename, self._ratefile)):
				raise Exception(SOX_CONV % (filename, self._ratefile))
			filename = self._ratefile

		wavFile = file(filename, 'rb')

		self.sphinx_rec.decode_raw(wavFile)
		result = self.sphinx_rec.get_hyp()

		return result[0]

	def listen(self, use_google = False):
		'''
		This function will perform speech recognition using either
		pocketsphinx or Google Speech API

		If pocketsphinx configuration was not passed in __init__
		or use_google is True, it will Google Speech API.
		Otherwise, pocketsphinx.
		'''
		self.notify_status(STATUS_WAITING)
		self.record_to_file(self._wavfile)
		self.notify_status(STATUS_PROCESSING)
		if (use_google or (self.sphinx_rec == None)):
			results = self.stt_google(self._wavfile)
		else:
			results = self.stt_sphinx(self._wavfile)
		return results

	def notify_status(self, status, val = None):
		if not self.statuscb : return
		self.statuscb(status, val)

	def __del__(self):
		_silentremove(self._wavfile)
		_silentremove(self._flacfile)
		_silentremove(self._ratefile)

class TTS(object):
	# google speech v2 api endpoint
	GOOGLE_TRANSLATE_URL = 'http://translate.google.com/translate_tts?tl=%s&q=%s'
	# using sox on OSX, replace with your own
	MP3_PLAY = 'play -q'
	# using 'say' as it's part of OSX, change to 'espeak' in Linux, for instance
	BACKUPPLAY = 'say'

	def __init__(self, lang_code):
		self.lang_code = lang_code
		fd, sndfile = tempfile.mkstemp(suffix = '.mp3')
		os.close(fd)
		self._mp3file = sndfile
		fd, sndfile = tempfile.mkstemp(suffix = '.wav')
		os.close(fd)
		self._wavfile = sndfile
		self._cachedMP3 = {}


	def read_out_loud(self, text, use_cache = False):
		try:
			filename = self.text_to_audio_file(text, use_cache)
			os.system(self.MP3_PLAY + ' ' + filename)
		except KeyboardInterrupt:
			raise
		except:
			print "Unexpected error:", sys.exc_info()[0]
			os.system(self.BACKUPPLAY + ' error in text to speech')

	def text_to_audio_file(self, text, use_cache = False, convert_to_wav = False):
		'''
		This will use Google for text-to-speech.

		If use_cache is True, TTS will checked _cachedSounds to see if it already
		translated this string to MP3 and avoid hitting Google servers.
		If it's not cached, it will cache it after.
		'''

		if use_cache and (text in self._cachedMP3):
			return self._cachedMP3[text]

		hrs = {
			"User-Agent": "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.63 Safari/535.7"
		}

		req = urllib2.Request(self.GOOGLE_TRANSLATE_URL %  (self.lang_code, urllib.quote_plus(text)), headers=hrs)
		
		try:
			p = urllib2.urlopen(req)
			sound_data = p.read()

			filename = self._mp3file

			if (use_cache) and (not convert_to_wav):
				fd, cachefile = tempfile.mkstemp(suffix = '.mp3')
				os.close(fd)
				filename = cachefile
				self._cachedMP3[text] = cachefile

			outfd = open(filename,'wb')
			outfd.write(sound_data)
			outfd.close()

			if convert_to_wav:
				wavfile = self._wavfile

				if use_cache:
					fd, wavfile = tempfile.mkstemp(suffix = '.wav')
					os.close(fd)

				os.system(SOX_CONV % (filename, wavfile))

				if use_cache:
					_silentremove(filename)
					self._cachedMP3[text] = wavfile

				filename = wavfile

			return filename
		except:
			raise
	
	def clean_cache(self):
		for filename in self._cachedMP3.values():
			_silentremove(filename)

		self._cachedMP3 = {}

	def __del__(self):
		_silentremove(self._mp3file)
		self.clean_cache()

class Conversation(object):
	def __init__(self, lang_code, api_key, sphinx_hmm = None, sphinx_lm = None, sphinx_dic = None, callback = None):
		self._lang_code = lang_code
		self._tts = TTS(lang_code)
		self._stt = STT(lang_code, api_key, sphinx_hmm, sphinx_lm, sphinx_dic, callback)
		# conversation context to be used by modules to persist information
		self.context = {}

	@property
	def lang_code(self):
		return self._lang_code

	@lang_code.setter
	def lang_code(self, value):
		self._lang_code = value
		self._tts.lang_code = value
		self._stt.lang_code = value

	@lang_code.deleter
	def lang_code(self):
		del self._lang_code

	def listen(self, use_google = False):
		val = self._stt.listen(use_google)
		self._stt.notify_status(STATUS_LISTENED, val)
		return val

	def say(self, text, use_cache = False):
		self._stt.notify_status(STATUS_SAID, text)
		self._tts.read_out_loud(text, use_cache)

	def calculate_silence(self, seconds = 5):
		return self._stt.calculate_silence(seconds)

class ConversationWithoutAudio(Conversation):
	def listen(self, use_google = False):
		return raw_input()

	def say(self, text, use_cache = False):
		print text

	def calculate_silence(self, seconds = 5):
		return 0

def _silentremove(filename):
			try:
				os.remove(filename)
			except OSError:
				pass