import requests, time, collections
import os

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
APP_POOL = os.getenv("ACTIVE_POOL")
ERROR_RATE_THRESHOLD = os.getenv("ERROR_RATE_THRESHOLD")
WINDOW_SIZE = os.getenv("WINDOW_SIZE")
ALERT_COOLDOWN_SEC = os.getenv("ALERT_COOLDOWN_SEC")

last_time = 0

dq = collections.deque([], WINDOW_SIZE)

with open("/var/log/nginx/access.log", "r") as f:
    
    while True:
        entries = f.readline()
        if not entries:
            print("no entry")
            time.sleep(0.2)
            continue
        
        logs = entries.splitlines()

        current_app_pool = logs[0].split(" - ")[1]
        
        if current_app_pool != previous_app_pool:
            if time.time() - last_time > ALERT_COOLDOWN_SEC:
                payload = {"text": f"application pool changed from {previous_app_pool} to {current_app_pool}"}
                requests.post(SLACK_WEBHOOK_URL, json=payload)
                previous_app_pool = current_app_pool
                last_time = time.time()
        else:
            previous_app_pool = current_app_pool

        code = logs[0].split(" - ")[4]
        dq.append(code)

        percentage = (sum(1 for c in dq if c.startswith("5"))  / len(dq)) * 100
        print(percentage, code)

        if percentage > ERROR_RATE_THRESHOLD and code.startswith("5") :
            payload = {"text": f"error rate has exceeded 30 percent"}
            requests.post(SLACK_WEBHOOK_URL, json=payload)
            
            


                
            


        
            

