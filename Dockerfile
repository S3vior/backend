FROM python:3.8-slim-buster

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && \
    apt-get install -y cmake && \
    apt-get install -y g++
RUN pip install -r requirements.txt

COPY . .

CMD [ "python", "main.py" ]
