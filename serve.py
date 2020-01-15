#!/usr/bin/env python3
import html
import re
import sys

import bottle
import requests
import sqlite3

import config

SERVER = 'https://mattermost.fsinf.at'
TOSS = 'https://toss.fsinf.at/api'
VOWI = 'https://vowi.fsinf.at'
CHANNEL_PREFIX = SERVER + '/w-inf-tuwien/channels/'
VOWI_TEAMID = 'sswtb6oqciyyfmkibh6mjz479w'

@bottle.get('/')
def index():
	return f'<h1>mattermost.fsinf.at glue API</h1>'\
			'<h2>Redirect to channel by course code</h2><pre>/channel_by_course_code/&lt;code></pre>'

def _mm_channel_name(title_de):
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
		chname = chname+'0'

	return chname

def mm_request(path, method='get', **kwargs):
	return requests.request(method, SERVER + '/api/v4' + path, **kwargs,
			headers={'Authorization': 'Bearer ' + config.MM_TOKEN})

@bottle.route('/channel_by_course_code/<code:re:[A-Z0-9]{6}>', method=('GET', 'POST'))
def channel_by_course_code(code):
	conn = sqlite3.connect('channels.db')
	cur = conn.cursor()
	cur.execute('SELECT name FROM channels WHERE code = ?', (code,))
	channel = cur.fetchone()
	if channel is None:
		res = requests.get(TOSS + '/courses/' + code)
		if res.status_code != 200:
			return bottle.HTTPError(404, 'Course not found')
		course = res.json()

		chname = _mm_channel_name(course['name_de'])
		cur.execute('SELECT 1 FROM channels WHERE name = ?', (chname,))

		if cur.fetchone() is not None:
			cur.execute('INSERT INTO channels (name, code) VALUES (?, ?)', (chname, code))
			bottle.redirect(CHANNEL_PREFIX + chname)

		channel = mm_request(f'/teams/{VOWI_TEAMID}/channels/name/{chname}')
		if channel.status_code == 200:
			bottle.redirect(CHANNEL_PREFIX + chname)
		else:
			res = requests.get(TOSS + course['machine']['instanceof'])
			inf_related = [gm['catalog']['subject_de'] in ('Informatik', 'Wirtschaftsinformatik')
				or gm['catalog']['name_de'] == 'Transferable Skills' for gm in  res.json()]
			if not any(inf_related):
				return 'mattermost.fsinf.at is only for informatics related courses and this course does not seem to be associated with Informatics, Business Informatics or the Transferable Skills.'
			if bottle.request.method == 'GET':
				return f'<p>There currently is no channel for <i>{html.escape(course["name_en"])}</i>, but you can create one:</p>'\
					f'<form method=post><button>Create channel "{html.escape(chname)}"</button></form>'
			else:
				res = mm_request('/channels', method='post', json={
					'team_id': VOWI_TEAMID,
					'name': chname,
					'display_name': course['name_de'][:64],
					'type': 'O'
				})
				if res.status_code != 201:
					print(res.json())
					return 'Channel creation failed'
				else:
					return bottle.redirect(CHANNEL_PREFIX + chname)
	else:
		bottle.redirect(CHANNEL_PREFIX + channel['name'])

if __name__ == '__main__':
	bottle.run()
