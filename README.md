# AWS Cloud Deployment Using Jenkins CI/CD Pipeline
### Enterprise-Grade Python Flask, AWS EC2, AWS S3, Gunicorn, Nginx & Jenkins DevOps Architecture

[![CI/CD Status](https://img.shields.io/badge/Jenkins-Pipeline%20Passed-brightgreen?logo=jenkins)](https://jenkins.io)
[![AWS](https://img.shields.io/badge/AWS-EC2%20%7C%20S3%20%7C%20IAM-orange?logo=amazon-aws)](https://aws.amazon.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.0-black?logo=flask)](https://flask.palletsprojects.com)
[![Web Server](https://img.shields.io/badge/Web%20Server-Nginx-009639?logo=nginx)](https://nginx.org)
[![Ubuntu](https://img.shields.io/badge/OS-Ubuntu%2024.04%20LTS-E95420?logo=ubuntu)](https://ubuntu.com)

---

## 1. Project Introduction

This project delivers an end-to-end, production-ready DevOps cloud deployment system for a Python Flask web application. It automates testing, packaging, archival, and continuous deployment to an **AWS EC2 (Ubuntu 24.04 LTS)** virtual machine through a declarative **Jenkins CI/CD Pipeline**.

Before each deployment, an automated backup tarball is created and uploaded to an encrypted, private **Amazon S3** bucket. The web application runs behind **Gunicorn** WSGI supervised by Linux **systemd**, reverse-proxied by **Nginx** on Port 80/443. The application features a real-time DevOps telemetry dashboard providing live host resource usage, EC2 instance metadata (IMDSv2), Jenkins pipeline execution state, and deployment audit tracking.

---

## 2. Project Objectives

- **Automated Source Retrieval:** Pull latest commits from GitHub upon trigger.
- **Dependency Isolation:** Provision and maintain isolated Python virtual environments.
- **Automated Quality Gate:** Execute test suites (`pytest`) and health checks prior to deployment.
- **Disaster Recovery & Backup:** Create pre-deployment snapshots and archive them to AWS S3.
- **Zero-Downtime Service Reload:** Seamlessly reload Gunicorn workers via Linux systemd.
- **Reverse Proxy & Edge Hardening:** Terminate web traffic with Nginx, apply security headers and rate limits.
- **Live Health Verification:** Automatically validate deployment success using the `/health` API.
- **Audit Logging:** Maintain a persistent deployment audit trail.

---

## 3. Technologies Used

| Category | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, Bootstrap 5, JavaScript, Chart.js, FontAwesome | DevOps Telemetry Dashboard |
| **Backend** | Python 3.10+, Flask 3.0, Gunicorn 21.2 | Application logic, REST APIs & WSGI server |
| **Cloud (AWS)** | AWS EC2 (Ubuntu 24.04 LTS), AWS S3, AWS IAM, Security Groups | Compute, encrypted backup storage, and network isolation |
| **Process Manager** | Linux systemd (`flaskapp.service`) | Auto-restart, fault recovery, and service lifecycle |
| **Web Server** | Nginx | Reverse proxy, static asset caching, Gzip compression, rate limiting |
| **DevOps / CI/CD** | Jenkins, Git, GitHub, Pytest, Bash scripting | Source control, automated build, test, backup, and deployment |

---

## 4. System Architecture

```
                       +-------------------------------------------------------+
                       |                     Developer Workstation             |
                       +-------------------------------------------------------+
                                                   |
                                            git push origin main
                                                   v
                       +-------------------------------------------------------+
                       |                   GitHub Repository                   |
                       +-------------------------------------------------------+
                                                   |
                                       Webhook / Polling Trigger
                                                   v
                       +-------------------------------------------------------+
                       |               Jenkins CI/CD Automation Node           |
                       |  [1. Checkout] -> [2. Build] -> [3. Test (pytest)]    |
                       +-------------------------------------------------------+
                                  |                                 |
                     [4. Upload Backup Tarball]           [5. SSH Deploy & Reload]
                                  v                                 v
        +------------------------------------+   +------------------------------------+
        |      AWS S3 Storage Bucket         |   |         AWS EC2 Instance           |
        |  (Private, AES-256 Encrypted)      |   |       (Ubuntu 24.04 LTS)           |
        |  s3://my-backups-bucket/backups/   |   |                                    |
        +------------------------------------+   |  +------------------------------+  |
                                                 |  | Nginx Reverse Proxy (:80)    |  |
                                                 |  +------------------------------+  |
                                                 |                 |                  |
                                                 |                 v                  |
                                                 |  +------------------------------+  |
                                                 |  | Gunicorn WSGI Workers        |  |
                                                 |  | (systemd: flaskapp.service)  |  |
                                                 |  +------------------------------+  |
                                                 |                 |                  |
                                                 |                 v                  |
                                                 |  +------------------------------+  |
                                                 |  | Python Flask App (:5000)     |  |
                                                 |  +------------------------------+  |
                                                 |                 |                  |
                                                 |  +--------------v---------------+  |
                                                 |  | [6. Health Check /health]    |  |
                                                 |  +------------------------------+  |
                                                 +------------------------------------+
```

---

## 5. Local Installation & Development

To test and run the project locally on your machine:

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/aws-cloud-deployment.git
cd aws-cloud-deployment
```

### 2. Set Up Virtual Environment
```bash
# On Linux / macOS
python3 -m venv venv
source venv/bin/activate

# On Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Local Environment Variables
Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```
*(On Windows PowerShell: `Copy-Item .env.example .env`)*

### 5. Run Automated Tests
```bash
pytest -v tests/test_app.py
```

### 6. Run the Application
```bash
python app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## 6. GitHub Configuration

To push this codebase to your own GitHub repository:

```bash
# 1. Initialize git repository if not already done
git init
git branch -M main

# 2. Add all files
git add .

# 3. Create initial commit
git commit -m "feat: complete AWS EC2 and Jenkins CI/CD deployment setup"

# 4. Add your GitHub remote repository
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/aws-cloud-deployment.git

# 5. Push to GitHub
git push -u origin main
```

---

## 7. AWS EC2 Provisioning (Ubuntu 24.04 LTS)

### Step 1: Launch EC2 Instance via AWS Console or AWS CLI
```bash
aws ec2 run-instances \
    --image-id resolve:ssm:/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id \
    --instance-type t3.micro \
    --key-name my-ec2-keypair \
    --security-group-ids sg-xxxxxxxxx \
    --subnet-id subnet-xxxxxxxxx \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=flask-app-prod}]'
```

### Step 2: Configure EC2 Security Group
Configure inbound rules in AWS VPC Security Group (`sg-xxxxxxxxx`):
- **Port 22 (SSH):** Inbound from `YOUR_IP/32` and `JENKINS_SERVER_IP/32`
- **Port 80 (HTTP):** Inbound from `0.0.0.0/0`
- **Port 443 (HTTPS):** Inbound from `0.0.0.0/0`
- **Port 5000 (Flask):** Keep internal only (do NOT expose to 0.0.0.0/0; Nginx proxies to it locally).

### Step 3: Run the Automated EC2 Setup Script
Connect to your EC2 instance via SSH:
```bash
ssh -i /path/to/my-ec2-keypair.pem ubuntu@<YOUR_EC2_PUBLIC_IP>
```

Clone the repository to `/var/www/flaskapp` and execute the bootstrap script:
```bash
sudo git clone https://github.com/<YOUR_GITHUB_USERNAME>/aws-cloud-deployment.git /var/www/flaskapp
cd /var/www/flaskapp
sudo chmod +x scripts/*.sh

# Run automated configuration
sudo ./scripts/setup_ec2.sh
```

The script will automatically:
1. Update system packages.
2. Install Python 3, Pip, Virtualenv, Git, Nginx, Curl, JQ, AWS CLI v2.
3. Create the `/var/www/flaskapp/venv` virtual environment and install `requirements.txt`.
4. Install and enable the systemd service `/etc/systemd/system/flaskapp.service`.
5. Install and enable the Nginx reverse proxy configuration `/etc/nginx/sites-available/flaskapp`.
6. Configure UFW firewall rules.
7. Start Gunicorn and Nginx, running a health check validation.

---

## 8. AWS S3 Configuration & IAM Role

### Step 1: Create a Dedicated, Private S3 Bucket
```bash
# Set your preferred bucket name and region
export S3_BUCKET_NAME="my-flaskapp-deploy-backups-bucket"
export AWS_REGION="us-east-1"

# Create S3 bucket
aws s3 mb "s3://${S3_BUCKET_NAME}" --region "${AWS_REGION}"

# Enable S3 Block Public Access (Enforce strict privacy)
aws s3api put-public-access-block \
    --bucket "${S3_BUCKET_NAME}" \
    --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Enable Server-Side Encryption (AES-256)
aws s3api put-bucket-encryption \
    --bucket "${S3_BUCKET_NAME}" \
    --server-side-encryption-configuration '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}'

# Enable Bucket Versioning
aws s3api put-bucket-versioning \
    --bucket "${S3_BUCKET_NAME}" \
    --versioning-configuration Status=Enabled
```

### Step 2: Configure IAM Least-Privilege Role for EC2
Create an IAM Policy allowing only necessary S3 actions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowS3BackupOperations",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-flaskapp-deploy-backups-bucket",
        "arn:aws:s3:::my-flaskapp-deploy-backups-bucket/*"
      ]
    }
  ]
}
```
Attach this IAM Role as an **Instance Profile** to your EC2 instance. This eliminates the need to hardcode AWS keys on the server!

---

## 9. Jenkins Installation

If you need to install Jenkins on a dedicated CI/CD server (Ubuntu 24.04 LTS):

```bash
# 1. Install OpenJDK 17
sudo apt update
sudo apt install -y openjdk-17-jdk

# 2. Add Jenkins Debian Repository Key
sudo wget -O /usr/share/keyrings/jenkins-keyring.asc \
  https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key

# 3. Add Jenkins Apt Repository
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/" | sudo tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null

# 4. Install Jenkins & Git
sudo apt update
sudo apt install -y jenkins git python3 python3-venv python3-pip rsync

# 5. Enable and start Jenkins
sudo systemctl enable jenkins
sudo systemctl start jenkins

# 6. Retrieve initial administrator password
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

Access Jenkins Web UI at: **`http://<YOUR_JENKINS_SERVER_IP>:8080`**

---

## 10. Jenkins Pipeline Configuration

### Step 1: Install Required Jenkins Plugins
In Jenkins UI: Navigate to **Manage Jenkins &rarr; Plugins &rarr; Available Plugins**, and install:
1. **Pipeline**
2. **Git Plugin**
3. **SSH Agent Plugin**
4. **Pipeline: AWS Steps** (or **AWS Credentials**)
5. **AnsiColor** (for formatted terminal logs)

### Step 2: Configure Credentials in Jenkins
Navigate to **Manage Jenkins &rarr; Credentials &rarr; System &rarr; Global credentials**:
1. **SSH Private Key for EC2:**
   - **Kind:** SSH Username with private key
   - **ID:** `ec2-ssh-key`
   - **Username:** `ubuntu`
   - **Private Key:** Paste your `.pem` key contents.
2. **AWS Credentials (Optional if Jenkins runs on EC2 with IAM role):**
   - **Kind:** AWS Credentials
   - **ID:** `aws-credentials`
   - **Access Key ID:** `AKIA...`
   - **Secret Access Key:** `wJalr...`

### Step 3: Create the Pipeline Job
1. Click **New Item**, enter `aws-cloud-deployment-pipeline`, select **Pipeline**, click **OK**.
2. Under **Build Triggers**, check **GitHub hook trigger for GITScm polling** (or Poll SCM).
3. Under **Pipeline**:
   - **Definition:** `Pipeline script from SCM`
   - **SCM:** `Git`
   - **Repository URL:** `https://github.com/<YOUR_USERNAME>/aws-cloud-deployment.git`
   - **Branch Specifier:** `*/main`
   - **Script Path:** `Jenkinsfile`
4. Click **Save**.

---

## 11. CI/CD Implementation (Pipeline Stages)

The included `Jenkinsfile` executes 6 deterministic stages:

```
[Stage 1: Checkout]  --> Clones repository, extracts commit metadata and author.
        |
[Stage 2: Build]     --> Creates isolated virtual environment, installs dependencies.
        |
[Stage 3: Test]      --> Runs pytest suite and syntax compilation gates.
        |
[Stage 4: Backup]    --> Archives codebase into tarball and uploads to AWS S3.
        |
[Stage 5: Deploy]    --> Rsyncs code to EC2 host, executes scripts/deploy.sh, reloads systemd.
        |
[Stage 6: Verify]    --> Probes /health endpoint; asserts HTTP 200 and healthy JSON response.
```

---

## 12. Application Deployment Scripts

| Script | Purpose | Usage |
| :--- | :--- | :--- |
| `scripts/setup_ec2.sh` | One-time server bootstrapping for Ubuntu 24.04 | `sudo ./scripts/setup_ec2.sh` |
| `scripts/deploy.sh` | Releases code updates, backs up, restarts service | `./scripts/deploy.sh main` |
| `scripts/backup.sh` | Creates compressed snapshot & pushes to S3 | `./scripts/backup.sh <bucket-name>` |
| `scripts/health_check.sh` | Tests `/health`, systemd status & Nginx | `./scripts/health_check.sh` |

---

## 13. Testing Procedures

### Running Unit and Integration Tests
```bash
pytest -v tests/test_app.py
```

Expected output:
```
============================= test session starts ==============================
collected 15 items

tests/test_app.py::test_home_page PASSED                                  [  6%]
tests/test_app.py::test_deployments_page PASSED                           [ 13%]
tests/test_app.py::test_infrastructure_page PASSED                        [ 20%]
tests/test_app.py::test_documentation_page PASSED                         [ 26%]
tests/test_app.py::test_health_check_endpoint PASSED                      [ 33%]
tests/test_app.py::test_api_status_endpoint PASSED                        [ 40%]
tests/test_app.py::test_api_system_info_endpoint PASSED                   [ 46%]
tests/test_app.py::test_api_deployments_get PASSED                        [ 53%]
tests/test_app.py::test_api_deployments_post PASSED                       [ 60%]
tests/test_app.py::test_api_backups_endpoint PASSED                       [ 66%]
tests/test_app.py::test_security_headers_present PASSED                   [ 73%]
tests/test_app.py::test_api_404_json_error PASSED                        [ 80%]
tests/test_app.py::test_get_git_info_returns_structure PASSED             [ 86%]
tests/test_app.py::test_get_ec2_metadata_returns_structure PASSED        [ 93%]
tests/test_app.py::test_get_jenkins_status_returns_structure PASSED     [100%]

============================== 15 passed in 0.45s ==============================
```

---

## 14. REST API Reference

### Health Check: `GET /health`
```bash
curl -i http://localhost:5000/health
```
```json
{
  "application": "AWS Cloud Deployment Portal",
  "environment": "production",
  "python_version": "3.10.12",
  "status": "healthy",
  "system_metrics": {
    "cpu_percent": 14.2,
    "disk_percent": 32.8,
    "memory_percent": 41.5
  },
  "uptime": "3d 4h 12m 45s",
  "uptime_seconds": 274365,
  "version": "1.0.0"
}
```

### Complete Telemetry Status: `GET /api/status`
Returns full payload containing EC2 metadata (IMDSv2), Jenkins state, Git commit details, S3 bucket connectivity, and hardware metrics.

### Deployment Audit: `GET /api/deployments` and `POST /api/deployments`
Retrieve past deployment history or record new deployment events programmatically from CI/CD runners.

---

## 15. Security Configuration & Best Practices

1. **IAM Roles over Hardcoded Credentials:**
   EC2 instance profiles and IAM roles are utilized instead of persistent AWS Access Key IDs.
2. **Private S3 Storage:**
   All public access to S3 backup buckets is blocked at the bucket level; default encryption with AES-256 is enforced.
3. **Defense in Depth Security Groups:**
   Port 5000 is bound strictly to `127.0.0.1` locally; only ports 80/443 and SSH (port 22 restricted by IP) are allowed inbound.
4. **Security Headers Enforced:**
   `X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection: 1; mode=block` are injected on every response.
5. **No Secrets in Version Control:**
   `.gitignore` prevents `.env`, SSH `.pem` keys, and local backup files from ever being committed to GitHub.
6. **HTTPS Guidance (Let's Encrypt / Certbot):**
   ```bash
   sudo apt install -y certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

---

## 16. Troubleshooting Runbook

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **502 Bad Gateway** | Gunicorn process is down | Run `sudo systemctl status flaskapp.service` and `sudo journalctl -u flaskapp -n 50`. Verify virtualenv path and port 5000 binding. |
| **Connection Refused on Port 80** | Nginx is stopped or UFW is blocking | Run `sudo systemctl status nginx` and `sudo ufw status`. Ensure port 80 is allowed. |
| **S3 Access Denied (Stage 4)** | Missing IAM permission | Check EC2 IAM role. Ensure `s3:PutObject` is granted on `arn:aws:s3:::<bucket-name>/*`. |
| **Jenkins SSH Stage Failed** | Host key verification or wrong key | Ensure Jenkins credential `ec2-ssh-key` contains the matching private key for user `ubuntu`. Check Security Group allows SSH from Jenkins IP. |
| **Permission Denied `/var/www/flaskapp`** | Incorrect directory ownership | Run `sudo chown -R ubuntu:ubuntu /var/www/flaskapp`. |

---

## 17. License
Distributed under the MIT License. Developed for enterprise AWS Cloud & DevOps engineering implementations.
