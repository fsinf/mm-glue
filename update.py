#!/usr/bin/env python3
import sqlite3
import collections

import utils

def update_channel(name : str, codes : list):
	header_parts = []
	for code in codes:
		res = utils.toss_get('/courses/' + code)
		if res.status_code == 200:
			# TODO: ignore outdated courses with same channel name but different course code
			header_parts.append(utils.channel_header(res.json()))
		else:
			print('TOSS did not find', code)
	header = ' | '.join(header_parts)

	res = utils.mm_request(f'/teams/{utils.VOWI_TEAMID}/channels/name/{name}')
	if res.status_code == 200:
		channel = res.json()
		utils.mm_request(method='put', path=f'/channels/{channel["id"]}/patch',
				json={'header': header})
	else:
		print('Mattermost did not find', name)

def update_all():
	conn = sqlite3.connect(utils.DBFILE)
	cur = conn.cursor()
	cur.execute('SELECT name, code FROM code_to_name')

	name2codes = collections.defaultdict(list)
	for result in cur.fetchall():
		name2codes[result[0]].append(result[1])

	for name, codes in name2codes.items():
		update_channel(name, codes)

if __name__ == '__main__':
	update_all()
