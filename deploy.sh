#!/bin/bash
set -e  # 오류 발생시 스크립트 중단


echo "deleting old app"
sudo rm -rf /var/www/back


echo "creating app folder"
sudo mkdir -p /var/www/back


echo "moving files to app folder"
sudo cp -r * /var/www/back/


# Navigate to the app directory and handle .env file
cd /var/www/back/
echo "Setting up .env file..."
if [ -f env ]; then
    sudo mv env .env
    sudo chown ubuntu:ubuntu .env
    echo ".env file created from env file"
elif [ -f .env ]; then
    sudo chown ubuntu:ubuntu .env
    echo ".env file already exists"
fi
# 111

# .env 파일 확인
echo "Checking .env file..."
if [ -f .env ]; then
    echo ".env file exists"
    ls -la .env
else
    echo "Warning: .env file not found"
fi


# 미니콘다 설치 (없는 경우)
if [ ! -d "/home/ubuntu/miniconda" ]; then
    echo "Installing Miniconda..."
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
    sudo chown ubuntu:ubuntu /tmp/miniconda.sh
    bash /tmp/miniconda.sh -b -p /home/ubuntu/miniconda
    rm /tmp/miniconda.sh
fi


# PATH에 미니콘다 추가
export PATH="/home/ubuntu/miniconda/bin:$PATH"
source /home/ubuntu/miniconda/bin/activate

# Update and install Nginx if not already installed
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


# 콘다 환경 생성 및 활성화
echo "Creating and activating conda environment..."
/home/ubuntu/miniconda/bin/conda create -y -n fastapi-env python=3.12 || true
source /home/ubuntu/miniconda/bin/activate fastapi-env


# 의존성 설치
echo "Installing dependencies..."
pip install -r requirements.txt


# Nginx 설정 테스트 및 재시작
echo "Testing and restarting Nginx..."
sudo nginx -t
sudo systemctl restart nginx


# 애플리케이션 시작
echo "Starting FastAPI application..."
cd /var/www/back
nohup /home/ubuntu/miniconda/envs/fastapi-env/bin/uvicorn app:app --host 0.0.0.0 --port 8000 --workers 3 > /var/log/fastapi/uvicorn.log 2>&1 &


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