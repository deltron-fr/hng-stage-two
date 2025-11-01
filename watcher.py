import os
import time
import collections
import requests
import docker
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
ACTIVE_POOL = os.getenv("ACTIVE_POOL", "blue")
ERROR_RATE_THRESHOLD = int(os.getenv("ERROR_RATE_THRESHOLD", 2))
WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", 200))
ALERT_COOLDOWN_SEC = int(os.getenv("ALERT_COOLDOWN_SEC", 300))


client = docker.from_env()
nginx_container = client.containers.get("nginx")

previous_app_pool = ACTIVE_POOL
last_failover_alert = 0
last_error_alert = 0
dq = collections.deque(maxlen=WINDOW_SIZE)

def post_slack(message):
    try:
        requests.post(SLACK_WEBHOOK_URL, json={"text": message})
    except Exception as e:
        print(f"Failed to send Slack alert: {e}")


for line in nginx_container.logs(stream=True, follow=True):
    try:
        log_line = line.decode().strip()
        if not log_line:
            continue

        parts = log_line.split(" - ")
        if len(parts) < 5:
            continue

        current_app_pool = parts[1]
        status_code = parts[4]

        if current_app_pool != previous_app_pool:
            if time.time() - last_failover_alert > ALERT_COOLDOWN_SEC:
                post_slack(f"Application pool changed from {previous_app_pool} to {current_app_pool}\nTime: {datetime.now(timezone.utc)}")
                last_failover_alert = time.time()
            previous_app_pool = current_app_pool

        dq.append(status_code)
        error_rate = (sum(1 for c in dq if c.startswith("5")) / len(dq)) * 100

        if error_rate > ERROR_RATE_THRESHOLD and status_code.startswith("5"):
            if time.time() - last_error_alert > ALERT_COOLDOWN_SEC:
                post_slack(f"Error rate exceeded {ERROR_RATE_THRESHOLD}% over last {WINDOW_SIZE} requests: {error_rate:.2f}%\nTime: {datetime.now(timezone.utc)}")
                last_error_alert = time.time()

    except Exception as e:
        print(f"Error processing log line: {e}")
