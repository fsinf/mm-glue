#!/usr/bin/env python3
import argparse
import collections
from datetime import datetime, timedelta
import sqlite3
import urllib.parse

import utils

MESSAGE_HEADER = '''``BOT-AUTODELETE-SLOW``
Folgende Seiten wurden in den letzten {} Stunden im VoWi bearbeitet:
'''

def spam_vowi_changes(cur, lasthours):
	rcend = int((datetime.now() - timedelta(hours=lasthours)).timestamp())
	res = utils.vowi_api(action='query', list='recentchanges', rcnamespace=3000, rclimit=500,
			rcshow='!bot|!redirect|!minor', rcend=rcend, format='json')
	res.raise_for_status()

	pagename2chname = {}
	chname2changes = collections.defaultdict(list)

	for change in res.json()['query']['recentchanges']:
		pagename = change['title'].split('/', maxsplit=1)[0]

		if pagename in pagename2chname:
			chname2changes[pagename2chname[pagename]].append(change)
			continue

		res = utils.vowi_api(action='askargs', printouts='Hat Kurs-ID', conditions=pagename, format='json')
		res.raise_for_status()
		query = res.json()['query']

		if query['results']:
			codes = query['results'][pagename]['printouts'].get('Hat Kurs-ID')
			if codes:
				cur.execute('SELECT name FROM code_to_name WHERE code = ?', (codes[0],))
				result = cur.fetchone()
				if result is None:
					continue
				pagename2chname[pagename] = result[0]
				chname2changes[result[0]].append(change)

	for chname, changes in chname2changes.items():
		res = utils.mm_api(f'/teams/{utils.VOWI_TEAMID}/channels/name/{chname}')
		if res.status_code != 200:
			print('mattermost did not find channel', chname)
			continue

		revids = {}
		old_revids = {}

		for change in changes:
			if change['title'] in revids:
				revids[change['title']] = max(revids[change['title']], change['revid'])
				old_revids[change['title']] = min(old_revids[change['title']], change['old_revid'])
			else:
				revids[change['title']] = change['revid']
				old_revids[change['title']] = change['old_revid']

		message = MESSAGE_HEADER.format(lasthours)

		for title, revid in revids.items():
			if old_revids[title] == 0:
				detail = 'NEW'
			else:
				diffpage = f'Special:Diff/{old_revids[title]}/{revid}'
				detail = f'[diff]({utils.VOWI_PAGE_PREFIX + diffpage})'
			if '/' in title:
				label = title.split('/', maxsplit=1)[1]
			else:
				label = title
			message += f'* [{label}]({utils.VOWI_PAGE_PREFIX + urllib.parse.quote(title)}) ({detail})\n'

		channel = res.json()
		res = utils.mm_api(method='post', path='/posts', json=dict(channel_id=channel['id'], message=message))
		if res.status_code != 201:
			print(f'[channel {chname}]: creating post failed:', res.json())
		else:
			print(f'[channel {chname}]: created post', res.json()['id'])

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Spam mattermost channels about VoWi changes.')
	parser.add_argument('lasthours', type=int, help='how many hours back to look for changes')
	args = parser.parse_args()
	conn = sqlite3.connect(utils.DBFILE)
	spam_vowi_changes(conn.cursor(), args.lasthours)
