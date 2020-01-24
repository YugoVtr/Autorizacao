FROM python:3.7-alpine
WORKDIR /app

ENV FLASK_APP app.py
ENV FLASK_RUN_HOST 0.0.0.0
ENV FLASK_ENV=development

RUN apk add --no-cache --update g++ gcc musl-dev linux-headers libressl-dev libffi-dev libxslt-dev

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
CMD ["flask", "run"]