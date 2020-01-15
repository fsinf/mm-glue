#!/usr/bin/env python3
import html
import sqlite3

import bottle

import utils

@bottle.get('/')
def index():
	return f'<h1>mattermost.fsinf.at glue API</h1>'\
			'<h2>Redirect to channel by course code</h2><pre>/channel_by_course_code/&lt;code></pre>'

def _infrelated(catalog):
	return catalog['subject_de'] in ('Informatik', 'Wirtschaftsinformatik')\
		or catalog['name_de'] == 'Transferable Skills'

@bottle.route('/channel_by_course_code/<code:re:[A-Z0-9]{6}>', method=('GET', 'POST'))
def channel_by_course_code(code):
	conn = sqlite3.connect(utils.DBFILE)
	cur = conn.cursor()
	cur.execute('SELECT name FROM code_to_name WHERE code = ?', (code,))
	channel = cur.fetchone()

	if channel is not None:
		return bottle.redirect(utils.CHANNEL_PREFIX + channel[0])

	res = utils.toss_get('/courses/' + code)
	if res.status_code != 200:
		return bottle.HTTPError(404, 'TOSS could not find this course')

	course = res.json()
	chname = utils.channel_name(course['name_de'])

	res = utils.mm_request(f'/teams/{utils.VOWI_TEAMID}/channels/name/{chname}')

	if res.status_code == 200:
		cur.execute('INSERT INTO code_to_name (code, name) VALUES (?, ?)', (code, chname))
		conn.commit()
		return bottle.redirect(utils.CHANNEL_PREFIX + chname)

	res = utils.toss_get(course['machine']['instanceof'])
	res.raise_for_status()

	if not any([_infrelated(gm['catalog']) for gm in res.json()]):
		return bottle.HTTPError(403, 'mattermost.fsinf.at is only for informatics related courses'\
				' and this course does not seem to be associated with'\
				' Informatics, Business Informatics or the Transferable Skills.')

	if bottle.request.method == 'GET':
		return f'<p>There currently is no channel for <i>{html.escape(course["name_en"])}</i>,'\
				' but you can create one:</p>'\
			f'<form method=post><button>Create channel "{html.escape(chname)}"</button></form>'

	elif bottle.request.method == 'POST':
		res = utils.mm_request('/channels', method='post', json={
			'team_id': utils.VOWI_TEAMID,
			'name': chname,
			'display_name': course['name_de'][:64],
			'header': utils.channel_header(course),
			'type': 'O'
		})
		if res.status_code == 201:
			cur.execute('INSERT INTO code_to_name (code, name) VALUES (?, ?)', (code, chname))
			conn.commit()
			return bottle.redirect(utils.CHANNEL_PREFIX + chname)
		else:
			print(res.json())
			return bottle.HTTPError(500, 'Channel creation failed')

if __name__ == '__main__':
	bottle.run()
