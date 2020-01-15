# TODO: filter by last updated
cur.execute('SELECT name, course_code name FROM channels')
for channel in cur.fetchall():
	requests.get(TOSS + '/courses/' + channel['course_code'])
# TODO: update channel header
# TODO: warn if archived
