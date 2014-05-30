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

# Reference for API:
# https://github.com/gillesdemey/google-speech-v2

class SKSTT(object):

	STATUS_LISTENING = 1
	STATUS_UPLOADING = 2

	# google speech v2 api endpoint
	GOOGLE_SPEECH_URL = 'https://www.google.com/speech-api/v2/recognize?output=json&lang=%s&key=%s'

	FLAC_CONV = 'flac -f'  # We need a WAV to FLAC converter. flac is available
						   # on Linux

	# pyaudio record settings
	THRESHOLD = 3000
	CHUNK_SIZE = 1024
	FORMAT = pyaudio.paInt16
	RATE = 44100

	SILENCE_STOP = 40

	def __init__(self, lang_code, api_key):
		self.lang_code = lang_code  # Language to use
		self.api_key = api_key


	# pieces of code obtained over daWEB
	# credits to unknown group of people

	def is_silent(self, snd_data):
		"Returns 'True' if below the 'silent' threshold"
		return max(snd_data) < self.THRESHOLD

	def normalize(self, snd_data):
		"Average the volume out"
		MAXIMUM = 16384
		times = float(MAXIMUM)/max(abs(i) for i in snd_data)

		r = array('h')
		for i in snd_data:
			r.append(int(i*times))
		return r

	def trim(self, snd_data):
		"Trim the blank spots at the start and end"
		def _trim(snd_data):
			snd_started = False
			r = array('h')

			for i in snd_data:
				if not snd_started and abs(i)>self.THRESHOLD:
					snd_started = True
					r.append(i)

				elif snd_started:
					r.append(i)
			return r

		# Trim to the left
		snd_data = _trim(snd_data)

		# Trim to the right
		snd_data.reverse()
		snd_data = _trim(snd_data)
		snd_data.reverse()
		return snd_data

	def add_silence(self, snd_data, seconds):
		"Add silence to the start and end of 'snd_data' of length 'seconds' (float)"
		r = array('h', [0 for i in xrange(int(seconds*self.RATE))])
		r.extend(snd_data)
		r.extend([0 for i in xrange(int(seconds*self.RATE))])
		return r

	def record(self):
		"""
		Record a word or words from the microphone and 
		return the data as an array of signed shorts.

		Normalizes the audio, trims silence from the 
		start and end, and pads with 0.5 seconds of 
		blank sound to make sure VLC et al can play 
		it without getting chopped off.
		"""
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

			silent = self.is_silent(snd_data)

			if snd_started:
				if silent:
					num_silent += 1
				else:
					num_silent = 0
			else:
				if not silent:
					snd_started = True

			if snd_started and num_silent > self.SILENCE_STOP:
				break

		sample_width = p.get_sample_size(self.FORMAT)
		stream.stop_stream()
		stream.close()
		p.terminate()

		r = self.normalize(r)
		r = self.trim(r)
		r = self.add_silence(r, 0.5)
		return sample_width, r

	def record_to_file(self,path):
		"Records from the microphone and outputs the resulting data to 'path'"
		sample_width, data = self.record()
		data = pack('<' + ('h'*len(data)), *data)

		wf = wave.open(path, 'wb')
		wf.setnchannels(1)
		wf.setsampwidth(sample_width)
		wf.setframerate(self.RATE)
		wf.writeframes(data)
		wf.close()

	def stt_google_wav(self, audio_fname):
		""" Sends audio file (audio_fname) to Google's text to speech 
			service and returns service's response. We need a FLAC 
			converter if audio is not FLAC (check FLAC_CONV). """

		#print "Sending", audio_fname
		#Convert to flac first
		filename = audio_fname
		del_flac = False
		if '.flac' not in filename:
			del_flac = True
			os.system(self.FLAC_CONV + ' ' + filename + ' 2>/dev/null')
			filename = filename.split('.')[0] + '.flac'

		f = open(filename, 'rb')
		flac_cont = f.read()
		f.close()

		# Headers. A common Chromium (Linux) User-Agent
		hrs = {"User-Agent": "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.63 Safari/535.7", 
			   'Content-type': 'audio/x-flac; rate=%s' % self.RATE}

		req = urllib2.Request(self.GOOGLE_SPEECH_URL %  (self.lang_code, self.api_key), data=flac_cont, headers=hrs)
		#print "Sending request to Google TTS"
		
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

		if del_flac:
			os.remove(filename)  # Remove temp file

		return res

	def listen_and_return(self, callback = None):
		fd,filename = tempfile.mkstemp(suffix = '.wav')
		if callback : callback(self.STATUS_LISTENING)
		self.record_to_file(filename)
		if callback : callback(self.STATUS_UPLOADING)
		results = self.stt_google_wav(filename)
		os.close(fd)
		os.remove(filename)
		return results

class SKTTS(object):
	# google speech v2 api endpoint
	GOOGLE_TRANSLATE_URL = 'http://translate.google.com/translate_tts?tl=%s&q=%s'
	# using sox on OSX, replace with your own
	MP3_PLAY = 'play -q'

	def __init__(self, lang_code):
		self.lang_code = lang_code

	def read_out_loud(self, text):
		hrs = {
			"User-Agent": "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.63 Safari/535.7"
		}

		req = urllib2.Request(self.GOOGLE_TRANSLATE_URL %  (self.lang_code, urllib.quote_plus(text)), headers=hrs)
		
		try:
			p = urllib2.urlopen(req)
			fd,filename = tempfile.mkstemp(suffix = '.mp3')
			outfd = os.fdopen(fd,'wb')
			outfd.write(p.read())
			outfd.close()
			os.system(self.MP3_PLAY + ' ' + filename)
			os.remove(filename)
		except KeyboardInterrupt:
			raise
		except:
			print "Couldn't parse service response"
			print "Unexpected error:", sys.exc_info()[0]
			raise
			res = None