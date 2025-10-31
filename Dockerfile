FROM python:3.12-slim

WORKDIR /watcher

COPY alert_logs.py requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "alert_logs.py"]