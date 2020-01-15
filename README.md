# mattermost.fsinf.at Glue

## Setup

	sudo apt-get install python3-bottle python3-requests

	adduser --disabled-password --gecos '' tossglue
	sudo su tossglue

	git clone https://github.com/fsinf/mm-glue ~/mm-glue
	cd ~/mm-glue

	sqlite3 database.sqlite < schema.sql
	cp config.py.example config.py
	# save a valid token

	crontab crontab.txt

	sudo cp tossglue.service /etc/systemd/system/
	sudo systemctl daemon-reload
	sudo systemctl enable tossglue
	sudo systemctl start tossglue
