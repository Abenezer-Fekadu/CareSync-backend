FROM bash
FROM python:3.12-alpine

WORKDIR /app
COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

COPY ./docker-entrypoint.sh /docker-entrypoint.sh
COPY .credentials.json /credentials.json
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]