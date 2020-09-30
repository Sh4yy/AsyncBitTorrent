

all:
	rm -rf torrent || true
	cp main.py torrent
	chmod 777 torrent
	rm -r pieces || true
	mkdir pieces || true

download:
	python3 main.py -a download


seed:
	python3 main.py -a seed
