FROM python:3.13-alpine

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY static/ ./static/
COPY templates/ ./templates/
COPY app.py .
COPY lidl.py .
COPY penny.py .
COPY run.sh .

RUN chmod +x start.sh

EXPOSE 5000

CMD ["./run.sh"]
