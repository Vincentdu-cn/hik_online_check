#!/bin/bash

# 获取当前时间
CURRENT_TIME=$(date +"%Y-%m-%d %H:%M:%S")

# 定义下载链接
IMAGE_URL="https://hik.com/hikcheck_v0.99.tar"

# 定义本地路径
HIKCHECK_DIR="/home/hikcheck"
IMAGE_FILE="$HIKCHECK_DIR/hikcheck_v0.99.tar"
ENV_FILE="$HIKCHECK_DIR/hik.env"

# 判断操作系统类型
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_NAME=$NAME
elif type lsb_release >/dev/null 2>&1; then
    OS_NAME=$(lsb_release -si)
else
    OS_NAME=$(uname -n)
fi
# 将OS_NAME转为小写
OS=$(echo "$OS_NAME" | tr '[:upper:]' '[:lower:]')

# 安装 wget
if ! command -v wget &> /dev/null; then
    echo "wget is not installed. Installing wget..."
    if [[ "$OS" == *"ubuntu"* || "$OS" == *"debian"* ]]; then
        sudo apt-get update
        sudo apt-get install -y wget
    elif [[ "$OS" == *"centos"* || "$OS" == *"red hat"* ]]; then
        sudo yum install -y wget
    else
        echo "Unsupported OS for automatic wget installation. Please install wget manually."
        exit 1
    fi
fi

# 安装 Docker
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "Docker installed successfully. Please log out and log back in to apply Docker group changes."
    exit 1
fi

# 创建目录（如果不存在）
mkdir -p "$HIKCHECK_DIR"

# 下载 Docker 镜像文件
echo "[$CURRENT_TIME]Downloading Docker image..."
wget -O "$IMAGE_FILE" "$IMAGE_URL"

# 加载 Docker 镜像
echo "[$CURRENT_TIME]Loading Docker image..."
docker load -i "$IMAGE_FILE"

# 开始创建env文件
# 定义默认值
DEFAULT_CRON_SCHEDULE="45 8 * * *"
DEFAULT_DEV_IP=172.16.110.200
DEFAULT_DEV_PASSWORD=hikpassword
DEFAULT_DEV_PORT=8000
DEFAULT_DEV_PROJECT=项目名称
DEFAULT_DEV_USERNAME=admin

# 校验 IPv4 地址格式
function validate_ip {
    local ip=$1
    if [[ $ip =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}$ ]]; then
        IFS='.' read -r -a octets <<< "$ip"
        for octet in "${octets[@]}"; do
            if [[ $octet -lt 0 || $octet -gt 255 ]]; then
                return 1
            fi
        done
        return 0
    else
        return 1
    fi
}

# 校验 Cron 表达式格式
function validate_cron {
    local cron=$1
    # 简化正则表达式，避免括号分组
    if [[ $cron =~ ^[0-9*]+[[:space:]]+[0-9*]+[[:space:]]+[0-9*]+[[:space:]]+[0-9*]+[[:space:]]+[0-9*]+$ ]]; then
        return 0
    else
        return 1
    fi
}

# 提示用户输入 CRON_SCHEDULE
while true; do
    read -p "Enter CRON_SCHEDULE [$DEFAULT_CRON_SCHEDULE]: " CRON_SCHEDULE
    CRON_SCHEDULE=${CRON_SCHEDULE:-$DEFAULT_CRON_SCHEDULE}
    if validate_cron "$CRON_SCHEDULE"; then
        break
    else
        echo "[$CURRENT_TIME]Invalid CRON_SCHEDULE format. Please enter a valid Cron expression (e.g., '45 8 * * *')."
    fi
done

# 提示用户输入 DEV_IP
while true; do
    read -p "Enter DEV_IP [$DEFAULT_DEV_IP]: " DEV_IP
    DEV_IP=${DEV_IP:-$DEFAULT_DEV_IP}
    if validate_ip "$DEV_IP"; then
        break
    else
        echo "[$CURRENT_TIME]Invalid DEV_IP format. Please enter a valid IPv4 address (e.g., '172.16.110.200')."
    fi
done

# 提示用户输入其他值
read -p "Enter DEV_PASSWORD [$DEFAULT_DEV_PASSWORD]: " DEV_PASSWORD
read -p "Enter DEV_PORT [$DEFAULT_DEV_PORT]: " DEV_PORT
read -p "Enter DEV_PROJECT [$DEFAULT_DEV_PROJECT]: " DEV_PROJECT
read -p "Enter DEV_USERNAME [$DEFAULT_DEV_USERNAME]: " DEV_USERNAME

# 如果用户未输入，则使用默认值
CRON_SCHEDULE=${CRON_SCHEDULE:-$DEFAULT_CRON_SCHEDULE}
DEV_IP=${DEV_IP:-$DEFAULT_DEV_IP}
DEV_PASSWORD=${DEV_PASSWORD:-$DEFAULT_DEV_PASSWORD}
DEV_PORT=${DEV_PORT:-$DEFAULT_DEV_PORT}
DEV_PROJECT=${DEV_PROJECT:-$DEFAULT_DEV_PROJECT}
DEV_USERNAME=${DEV_USERNAME:-$DEFAULT_DEV_USERNAME}


# 写入环境变量文件
cat <<EOF > "$ENV_FILE"
CRON_SCHEDULE="$CRON_SCHEDULE"
DEV_IP=$DEV_IP
DEV_PASSWORD=$DEV_PASSWORD
DEV_PORT=$DEV_PORT
DEV_PROJECT=$DEV_PROJECT
DEV_USERNAME=$DEV_USERNAME
EOF

echo "[$CURRENT_TIME]Environment file created at $ENV_FILE"

# 运行 Docker 容器
echo "[$CURRENT_TIME]Running Docker container..."
docker run -d --name 1hikcheck -v "$ENV_FILE:/app/.env" hikcheck:v0.99

echo "[$CURRENT_TIME]Docker container is running."
