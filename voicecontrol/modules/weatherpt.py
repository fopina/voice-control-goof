# coding=UTF-8

import urllib,urllib2
import json
from datetime import datetime

WEATHER_CODES = {
	200: 'trovoada com chuva ligeira',
	201: 'trovoada com chuva',
	202: 'trovoada com chuva intensa',
	210: 'trovoada ligeira',
	211: 'trovoada',
	212: 'trovoada forte',
	221: 'períodos de trovoada',
	230: 'trovoada com chuviscos ligeiros',
	231: 'trovoada com chuviscos',
	232: 'trovoada com chuviscos intensos',
	300: 'chuviscos ligeiros',
	301: 'chuviscos',
	302: 'chuviscos intensos',
	310: 'chuva ligeira',
	311: 'chuva ligeira',
	312: 'chuva intensa',
	313: 'aguaceiros',
	314: 'aguaceiros fortes e chuviscos',
	321: 'chuviscos',
	500: 'chuva fraca',
	501: 'chuva moderada',
	502: 'chuva intensa',
	503: 'chuva muito forte',
	504: 'chuva muito forte',
	511: 'chuva gelada',
	520: 'aguaceiros fracos',
	521: 'aguaceiros',
	522: 'aguaceiros fortes',
	531: 'períodos de aguaceiros',
	600: 'nevão ligeiro',
	601: 'neve',
	602: 'nevão forte',
	611: 'chuva com neve',
	612: 'aguaceiro de neve',
	615: 'chuva ligeira e neve',
	616: 'chuva e neve',
	620: 'aguaceiros ligeiro de neve',
	621: 'aguaceiros de neve',
	622: 'aguaceiros intensos de neve',
	701: 'neblina ou nevoeiro',
	711: 'fumo',
	721: 'nevoeiro',
	731: 'turbilhões de areia/poeira',
	741: 'nevoeiro',
	751: 'areia',
	761: 'poeira',
	762: 'cinza vulcânica',
	771: 'rajadas',
	781: 'tornado',
	800: 'céu limpo',
	801: 'algumas nuvens',
	802: 'nuvens dispersas',
	803: 'céu nublado',
	804: 'céu muito nublado',
	900: 'tornado',
	901: 'tempestade tropical',
	902: 'furacão',
	903: 'frio',
	904: 'quente',
	905: 'ventoso',
	906: 'granizo',
	950: 'ambiente',
	951: 'calmia',
	952: 'brisa ligeira',
	953: 'brisa suave', 
	954: 'brisa moderada',
	955: 'brisa fresca',
	956: 'brisa forte',
	957: 'vento forte a muito forte',
	958: 'vento muito forte', 
	959: 'vento muito forte',
	960: 'tempestade', 
	961: 'tempestade violenta',
	962: 'furacão'
}

def add_day(day_name, days):
	return (day_name, days)

def week_day(day_name, weekday):
	current_weekday = datetime.now().isoweekday()
	diff = (weekday - 1 - current_weekday) % 7 + 1
	if weekday <= 1:
		next_name = 'próximo ' + day_name
	else:
		next_name = 'próxima ' + day_name

	return (next_name, diff)

named_days = {
	('amanhã', add_day, 1),
	('domingo', week_day, 0),
	('segunda', week_day, 1),
	('terça', week_day, 2),
	('quarta', week_day, 3),
	('quinta', week_day, 4),
	('sexta', week_day, 5),
	('sábado', week_day, 6),
}

def valid_input(conversation, input):
	if 'tempo' in input : return True
	if 'temperatura' in input : return True
	return False

def process_input(conversation, input):
	future_day = 0
	temp_current = None
	day = None

	for day_name, day_meth, day_value in named_days:
		if day_name in input:
			day, future_day = day_meth(day_name, day_value)

	if not day:
		day = 'hoje'

	if 'depois' in input:
		future_day += 1
		day = 'depois de ' + day
	
	if future_day:
		wdata = check_forecast('Porto', 'PT', future_day + 1)['list'][-1]
		temp_min = wdata['temp']['min']
		temp_max = wdata['temp']['max']
		condition = wdata['weather']
	else:
		wdata = check_weather('Porto', 'PT')
		temp_current = wdata['main']['temp']
		temp_min = wdata['main']['temp_min']
		temp_max = wdata['main']['temp_max']
		condition = wdata['weather']

	if temp_current:
		conversation.say('Temperatura actual de %s graus.' % temp_current)

	conversation.say('Prevê-se para %s temperatura mínima de %s e máxima de %s.' % (day, temp_min, temp_max))

	desc = []
	if condition:
		for entry in condition:
			if entry['id'] in WEATHER_CODES:
				desc.append(WEATHER_CODES[entry['id']])

	if desc:
		conversation.say('Probabilidades de ' + ' e '.join(desc))
		
	return None

def check_weather(city, country, units = 'metric'):
	url = 'http://api.openweathermap.org/data/2.5/weather?q=%s,%s&units=%s' % (city, country, units)
	req = urllib2.Request(url)
	data = json.loads(urllib2.urlopen(req).read())
	return data

def check_forecast(city, country, future_days, units = 'metric'):
	url = 'http://api.openweathermap.org/data/2.5/forecast/daily?q=%s,%s&units=%s&cnt=%d' % (city, country, units, future_days)
	req = urllib2.Request(url)
	data = json.loads(urllib2.urlopen(req).read())
	return data

if __name__ == '__main__':
	data = check_weather('London','UK')
	print data['main']['temp']
	for entry in data['weather']:
		print WEATHER_CODES.get(entry['id'])