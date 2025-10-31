FROM python:3.12-slim

WORKDIR /watcher

COPY watcher.py requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "watcher.py"]