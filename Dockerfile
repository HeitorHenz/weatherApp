FROM python:3.12.2

ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt

COPY . /app

EXPOSE 9999

CMD ["fastapi", "dev", "src/main.py", "--port", "9999", "--host", "0.0.0.0"]
