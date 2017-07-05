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
	DEBUG=1 ${PYTHON} manage.py compilemessages

c:        ## Clean compiled pyc files.
	find kirppu -name \*.pyc -exec rm {} +
	find kirppuauth -name \*.pyc -exec rm {} +
	find kirppu_project -name \*.pyc -exec rm {} +

apistub:  ## Create/update ajax_api stub file helping navigation from frontend code to backend.
	find kirppu -name \*.py -exec grep -A 1 '@ajax_func' {} + | awk '\
	BEGIN { print("throw \"Don'\''t use\";\nApi = {"); }\
	/py-def/ { a[0] = "";\
		match($$0, "^(.*/)?(.+).py-def ([[:alnum:]_]+)\\(", a);\
		printf("    %s: function() {/**\n", a[3]);\
		printf("        %s.%s", a[2], a[3]);\
		printf("\n    */},\n");\
	}\
	END { print("};"); }' > kirppu/static_src/js/api_stub.js

help:     ## This help.
	@fgrep -h "#""#" $(MAKEFILE_LIST) | sed -e "s/:\\s*#""#/\n\t/"
