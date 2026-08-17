FROM python:3.14

WORKDIR /app

COPY ./requirements.txt requirements.txt
COPY ./.env .env
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./app .

CMD ["fastapi", "run", "main.py", "--port", "80"]