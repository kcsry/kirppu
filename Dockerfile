FROM python:3.6
WORKDIR /usr/src/app

RUN curl -sL https://deb.nodesource.com/setup_8.x | bash - && \
    apt-get -y install nodejs gettext && \
    mkdir -p /usr/src/app/kirppu

COPY requirements.txt requirements-oauth.txt requirements-production.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt -r requirements-oauth.txt -r requirements-production.txt

COPY . /usr/src/app
RUN cd /usr/src/app/kirppu && \
    npm install && \
    npm run gulp && \
    rm -rf node_modules && \
    groupadd -r kirppu && useradd -r -g kirppu kirppu

RUN env DEBUG=1 python manage.py collectstatic --noinput && \
    env DEBUG=1 python manage.py compilemessages && \
    python -m compileall -q .

USER kirppu
EXPOSE 8000
CMD ["python", "manage.py", "docker_start"]
