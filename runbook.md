## Runbook: Handling Blue/Green Failovers and 5xx Error rates

**Last Updated**: 01-11-2025
**Severity**: High
**Team**: DevOps Team
**Category**: Incident Response

---

## 1. Summary

Blue/Green Failovers and 5xx Errors usually indicate server failures such as:
- Application crash or unhandled exception
- Database connection failure
- Server Overload, etc

---

## 2. Detection

### Automated Alerts:
- Automated alerts are sent to a Slack channel containing a detailed message of the issue. Example:
    - **_Application pool changed from blue to green_** - this means there was an error on the current pool(blue in this case) and nginx switched to the green deployment pool to avoid downtime. 
    - **_error rate exceeded 2% over last 200 requests_** - this means that the percentage of error status codes(5xx) over a max window of 200 http requests has exceeded 2% 


---

## 3. Operator Actions

1. **Validate alert** - If alert concerns application pool change or 5xx error rates, to confirm check the logs:
    ```
    docker logs nginx(container-name)
    ```

    Or check the health of the application:
    ```
    curl http://<ip-address>:8080/version -v
    ```

2. **Go through the application logs** - Check the docker application logs for both application pools. Example command:

    ```
    docker logs <container_name>
    ```

3. **Rollback to a previous working Deployment** - Using a version control system, rollback to a previous working commit and deploy that version to production.

    - To check the commit:
        ```
        git log
        ```
    - To rollback:
        ```
        git revert <commit-hash>
        ```

---

## 4. Escalation

- **If 5xx persists:**  
  - Notify on-call **Backend** engineers  
  - Create an incident ticket

---

## 5. Post-Incident Actions

- Gather metrics from before/during/after incident  
- Perform root cause analysis
- Document fix and preventive measures    
