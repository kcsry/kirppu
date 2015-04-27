PYTHON=python
.PHONY: default none messages compile c help
LOCS=-l fi -l en
MM_ARGS=${LOCS} -i KirppuVenv -i node_modules --no-location

default: help

none:

messages: ## Extract strings from sources for localization.
	${PYTHON} manage.py makemessages -d djangojs ${MM_ARGS}
	${PYTHON} manage.py makemessages -d django ${MM_ARGS}

static:   ## Install npm dependencies and build static files.
	cd kirppu && npm i && gulp pipeline

compile:  ## Compile localizations for use.
	${PYTHON} manage.py compilemessages

c:        ## Clean compiled pyc files.
	find kirppu -name \*.pyc -exec rm {} +
	find kirppuauth -name \*.pyc -exec rm {} +
	find kirppu_project -name \*.pyc -exec rm {} +

help:     ## This help.
	@fgrep -h "#""#" $(MAKEFILE_LIST) | sed -e "s/:\\s*#""#/\n\t/"
