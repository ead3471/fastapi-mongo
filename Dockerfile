FROM python:3.11
WORKDIR /app

ADD ./src/requirements.txt /app/requirements.txt

RUN pip install --upgrade -r requirements.txt

EXPOSE 8080

COPY ./src /app

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]