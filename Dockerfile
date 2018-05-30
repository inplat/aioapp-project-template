FROM python:3.6-alpine

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/

RUN apk --virtual deps --no-cache add gcc linux-headers musl-dev \
  && pip install --no-cache-dir -r requirements.txt \
  && apk del deps


COPY . /usr/src/app

CMD [ "python", "-u", "-m", "myaioapp.cli" ]
