FROM python:3.9-slim-buster

RUN mkdir /code

WORKDIR /code

COPY requirements.txt .

RUN apt-get update && apt-get install -y git
RUN apt-get update && apt-get install docker.io -y
RUN apt-get update -y && apt-get install -y gcc
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host=0.0.0.0", "--port=8000"]