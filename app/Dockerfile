FROM python:3.8-alpine
RUN apk add build-base
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY ./ ./
