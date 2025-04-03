#!/bin/bash
set -e  # 오류 발생시 스크립트 중단

# 디스크 공간 확인
echo "Initial disk space usage:"
df -h

# pip 임시 디렉토리 정리
echo "Cleaning pip cache..."
rm -rf ~/.cache/pip
rm -rf /tmp/pip-*
rm -rf /tmp/build
rm -rf /tmp/wheel*

# 시스템 캐시 및 임시 파일 정리
echo "Performing deep cleanup..."
sudo apt-get clean
sudo apt-get autoremove -y
sudo apt-get purge -y
sudo rm -rf /var/lib/apt/lists/*
sudo rm -rf /tmp/*
sudo rm -rf ~/.cache/conda
sudo rm -rf /var/cache/apt/archives/*
sudo rm -rf /var/log/journal/*
sudo journalctl --vacuum-time=1d

# Python 관련 캐시 파일 정리
echo "Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete
find . -type d -name "*.egg-info" -exec rm -rf {} +
find . -type d -name "*.egg" -exec rm -rf {} +
find . -type d -name ".pytest_cache" -exec rm -rf {} +
find . -type d -name ".coverage" -exec rm -rf {} +
find . -type d -name "htmlcov" -exec rm -rf {} +

# 기존 배포 파일 정리
echo "Cleaning up old deployments..."
sudo systemctl stop nginx || true
sudo pkill uvicorn || true
sudo rm -rf /var/www/back
sudo rm -rf /var/log/fastapi/*
sudo rm -rf /var/log/nginx/*

echo "Current disk space usage:"
df -h

echo "creating app folder"
sudo mkdir -p /var/www/back

echo "moving files to app folder"
sudo cp -r * /var/www/back/

# Navigate to the app directory and handle .env file
cd /var/www/back/
echo "Setting up .env file..."

# .env 파일 생성
if [ -n "$DB_VARIABLES" ]; then
    echo "$DB_VARIABLES" | sudo tee .env > /dev/null
    sudo chown ubuntu:ubuntu .env
    echo ".env file created from DB_VARIABLES"
elif [ -f env ]; then
    sudo mv env .env
    sudo chown ubuntu:ubuntu .env
    echo ".env file created from env file"
elif [ -f .env ]; then
    sudo chown ubuntu:ubuntu .env
    echo ".env file already exists"
else
    echo "Warning: No environment variables found"
    exit 1
fi

# .env 파일 확인
echo "Checking .env file..."
if [ -f .env ]; then
    echo ".env file exists"
    ls -la .env
else
    echo "Error: .env file not found"
    exit 1
fi

# Conda 환경 관리
echo "Setting up conda environment..."

# 미니콘다 설치 (없는 경우)
if [ ! -d "/home/ubuntu/miniconda" ]; then
    echo "Installing Miniconda..."
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
    bash /tmp/miniconda.sh -b -p /home/ubuntu/miniconda
    rm /tmp/miniconda.sh
    
    # Miniconda 초기화
    /home/ubuntu/miniconda/bin/conda init bash
    source ~/.bashrc
fi

# PATH에 Miniconda 추가
export PATH="/home/ubuntu/miniconda/bin:$PATH"

# Conda 초기화 및 환경 설정
if [ -f "/home/ubuntu/miniconda/bin/activate" ]; then
    source /home/ubuntu/miniconda/bin/activate
    
    # Conda 환경 완전 정리
    echo "Removing all conda environments..."
    conda remove --name fastapi-env --all -y || true
    conda clean --all -y
    
    # 기존 환경이 있으면 삭제하고 새로 생성
    conda env remove -n fastapi-env --yes || true
    conda create -n fastapi-env python=3.12 -y
    conda activate fastapi-env
else
    echo "Error: Miniconda activate script not found"
    exit 1
fi

# Nginx 설치 및 설정
if ! command -v nginx > /dev/null; then
    echo "Installing Nginx"
    sudo apt-get update
    sudo apt-get install -y nginx
fi

# Nginx 설정
echo "Configuring Nginx..."
sudo bash -c 'cat > /etc/nginx/sites-available/myapp <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF'

# Nginx 설정 심볼릭 링크 생성
sudo ln -sf /etc/nginx/sites-available/myapp /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 로그 파일 설정
sudo mkdir -p /var/log/fastapi
sudo touch /var/log/fastapi/uvicorn.log
sudo chown -R ubuntu:ubuntu /var/log/fastapi

# 기존 프로세스 정리
echo "Cleaning up existing processes..."
sudo pkill uvicorn || true
sudo systemctl stop nginx || true

# 애플리케이션 디렉토리 권한 설정
sudo chown -R ubuntu:ubuntu /var/www/back

# 의존성 설치
echo "Installing dependencies..."
# pip 캐시 사용하지 않고 설치
pip install --no-cache-dir --no-deps -r requirements.txt

# 나머지 의존성 설치
pip install --no-cache-dir -r requirements.txt

# Nginx 설정 테스트 및 재시작
echo "Testing and restarting Nginx..."
sudo nginx -t
sudo systemctl restart nginx

# 애플리케이션 시작
echo "Starting FastAPI application..."
cd /var/www/back

# 기존 프로세스 정리
sudo pkill uvicorn || true

# ubuntu 사용자로 uvicorn 실행
sudo -u ubuntu bash -c 'cd /var/www/back && nohup python -m uvicorn app:app --host 0.0.0.0 --port 8000 --workers 3 --log-level debug > /var/log/fastapi/uvicorn.log 2>&1 &'

# 애플리케이션 시작 확인을 위한 대기
sleep 5

# 로그 확인
echo "Recent application logs:"
tail -n 20 /var/log/fastapi/uvicorn.log || true

echo "Deployment completed successfully! 🚀"

# 상태 확인
echo "Checking service status..."
ps aux | grep uvicorn
sudo systemctl status nginx

# 2