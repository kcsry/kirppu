PYTHON=python
.PHONY: none messages compile
LOCS=-l fi -l en
MM_ARGS=${LOCS} -i KirppuVenv -i node_modules --no-location

none:

messages:
	${PYTHON} manage.py makemessages -d djangojs ${MM_ARGS}
	${PYTHON} manage.py makemessages -d django ${MM_ARGS}

static:
	cd kirppu && npm i && gulp pipeline

compile:
	${PYTHON} manage.py compilemessages
