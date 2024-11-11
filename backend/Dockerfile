FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*


COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

ENV FLASK_APP=main.py
ENV FLASK_RUN_HOST=0.0.0.0

CMD ["flask", "run"]
