# coding=UTF-8

def valid_input(conversation, input):
	if conversation.lang_code == 'pt-PT':
		if 'olá' in input : return True
	return False

def process_input(conversation, input):
	processed = False
	if conversation.context.get('name'):
		conversation.say('Olá, ' + conversation.context['name'])
		processed = True
	else:
		conversation.say('Olá, como te chamas?')
		name = conversation.listen(use_google = True)
		if name:
			conversation.context['name'] = name
			conversation.say('Olá, ' + conversation.context['name'])
			processed = True

	return (processed, None)