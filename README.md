# mattermost.fsinf.at Glue

## Setup

	sudo useradd -r -m tossglue
	sudo loginctl enable-linger tossglue
	sudo apt install python3-pip
	sudo su - tossglue

	git clone https://github.com/fsinf/mm-glue
	cd ~/mm-glue
	
	pip3 install --user --upgrade -r requirements.txt 
	sqlite3 database.sqlite < schema.sql
	cp config.py.example config.py
	# save a valid token

	crontab crontab.txt

	mkdir -p ~/.config/systemd/user/
	cp tossglue.service ~/.config/systemd/user/
	XDG_RUNTIME_DIR=/run/user/$UID systemctl --user daemon-reload
	XDG_RUNTIME_DIR=/run/user/$UID systemctl --user enable systemd-tmpfiles-setup.service systemd-tmpfiles-clean.timer tossglue.service
	XDG_RUNTIME_DIR=/run/user/$UID systemctl --user start systemd-tmpfiles-setup.service systemd-tmpfiles-clean.timer tossglue.service
