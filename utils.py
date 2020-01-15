import re

import requests

import config

_MATTERMOST = 'https://mattermost.fsinf.at'
_MATTERMOST_API = _MATTERMOST + '/api/v4'
_TOSS_API = 'https://toss.fsinf.at/api'
_VOWI_API = 'https://vowi.fsinf.at/api.php'
_USER_AGENT = 'MM-Glue (https://github.com/fsinf/mm-glue)'

CHANNEL_PREFIX = _MATTERMOST + '/w-inf-tuwien/channels/'
VOWI_TEAMID = 'sswtb6oqciyyfmkibh6mjz479w'
DBFILE = 'database.sqlite'

def mm_request(path, method='get', **kwargs):
	return requests.request(method, _MATTERMOST_API + path, **kwargs,
			headers={'Authorization': 'Bearer ' + config.MM_TOKEN,
				'User-Agent': _USER_AGENT})

def toss_get(path, **kwargs):
	return requests.get(_TOSS_API + path, **kwargs, headers={'User-Agent': _USER_AGENT})

def channel_name(title_de):
	title_de = title_de.replace('für Informatik und Wirtschaftsinformatik', '')
	chname = title_de.lower().replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
	chname = re.sub('[^a-zA-Z0-9_]', '-', chname)
	chname = re.sub('-+', '-', chname)
	chname = chname[:63]
	chname = chname.strip('-')

	# now even group-channels (len == 40) do weird shit. Thanks MM :/
	# Heisen-Issue: for some reason MM uses sometimes the channel name as id if
	# len == 26 gives and when switching between teams.
	if len(chname) == 54 or len(chname) == 40 or len(chname) == 26:
		chname = chname + '0'

	return chname

def channel_header(course):
	return f'{course["course_type"]} ({course["first_lecturer_lastname"]}): '\
		+ ', '.join([f'[{label}]({url})' for label, url in course['human'].items()
	                  if label != 'mattermost'])
