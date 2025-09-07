FROM python:3.11.11-slim

RUN apt-get update && apt-get install -y libgl1 libglib2.0-0

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

EXPOSE 8008

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8008"]
