# Oracle Linux 9 Deployment Guide

Use this checklist to deploy the FastAPI chatbot backend on an Oracle Linux 9
server listening on TCP port `20001`.

## 1. Prepare the repository
- Add your secrets to `.env` (values can be empty placeholders for now).
- Run `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
  locally to confirm the dependency set resolves.
- Commit everything, then push to your remote Git repository so the server can clone it.

## 2. Provision the server
- Update system packages: `sudo dnf update -y`.
- Install runtimes and build tools: `sudo dnf install -y git python3 python3-venv`
  (add `python3-pip` and compiler packages if they are not present).
- Create an unprivileged app user if desired:
  `sudo useradd --system --create-home --shell /sbin/nologin apichatbot`.

## 3. Upload configuration
- Copy the `.env` file (containing `AZURE_OPENAI_*` and `CHATBOT_API_BASE_URL`) to the server.
- Store the file under `/opt/apichatbot/.env` or the deployed user's home directory.
- Ensure only the service account can read it: `sudo chmod 600 /opt/apichatbot/.env`.

## 4. Deploy the application code
- Become the deployment user (`sudo -u apichatbot -s`) or work as your admin account.
- Clone the repository, e.g. `git clone https://<your-remote>/apichatbot.git /opt/apichatbot`.
- From the project directory create the virtual environment:
  `python3 -m venv /opt/apichatbot/.venv`.
- Install dependencies:
  ```
  source /opt/apichatbot/.venv/bin/activate
  pip install --upgrade pip
  pip install -r /opt/apichatbot/requirements.txt
  deactivate
  ```

## 5. Configure a systemd service (recommended)
Create `/etc/systemd/system/apichatbot.service` with:
```
[Unit]
Description=FastAPI AI Chatbot
After=network.target

[Service]
User=apichatbot
Group=apichatbot
WorkingDirectory=/opt/apichatbot
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=/opt/apichatbot/.env
ExecStart=/opt/apichatbot/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 20001
Restart=on-failure

[Install]
WantedBy=multi-user.target
```
- Reload systemd: `sudo systemctl daemon-reload`.
- Start the service: `sudo systemctl start apichatbot`.
- Enable on boot: `sudo systemctl enable apichatbot`.

## 6. Open the firewall
- Allow inbound traffic on the application port:
  ```
  sudo firewall-cmd --permanent --add-port=20001/tcp
  sudo firewall-cmd --reload
  ```
- If SELinux is enforcing, allow the port for HTTP services:
  `sudo semanage port -a -t http_port_t -p tcp 20001` (install `policycoreutils-python-utils` if missing).

## 7. Verify the deployment
- Confirm the service is running: `sudo systemctl status apichatbot`.
- Check logs if needed: `sudo journalctl -u apichatbot -f`.
- From a remote host: `curl http://<server-ip>:20001/health/ready` should return `{"status":"ok"}`.

## 8. Updating the application
- Pull the latest code: `cd /opt/apichatbot && sudo -u apichatbot git pull`.
- Reinstall dependencies if `requirements.txt` changed:
  `sudo -u apichatbot /opt/apichatbot/.venv/bin/pip install -r requirements.txt`.
- Restart the service: `sudo systemctl restart apichatbot`.

