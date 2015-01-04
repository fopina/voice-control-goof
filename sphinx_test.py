#!/usr/bin/env python
# coding=UTF-8


'''
This was originally done to test against jasper.wav from jasperproject
as the trigger word used is that one (and the only use for sphinx)
'''

from voicecontrol.ttsstt import STT
import sys

try:
	from config import API_KEY, DEFAULT_LOCALE
	from config import SPHINX_LM, SPHINX_DIC, SPHINX_HMM
except:
	raise Exception('config.py not found, please copy config.py.example to config.py')

def main():
	stt = STT(DEFAULT_LOCALE, API_KEY, SPHINX_HMM, SPHINX_LM, SPHINX_DIC)
	print stt.stt_sphinx(sys.argv[1])

if __name__ == '__main__':
	main()