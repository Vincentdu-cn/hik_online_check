#!/bin/sh

# 获取当前时间
CURRENT_TIME=$(date +"%Y-%m-%d %H:%M:%S")

# 检查 /app/.env 文件是否存在
if [ -f "/app/.env" ]; then
    echo "[$CURRENT_TIME].env file found, loading environment variables..."
    . /app/.env
else
    echo "[$CURRENT_TIME].env file not found."
fi

# 获取环境变量
CRON_SCHEDULE=${CRON_SCHEDULE:-"40 8 * * *"}

PYTHON_PATH=$(which python3)

# 创建crontab文件内容
echo "${CRON_SCHEDULE} ${PYTHON_PATH} /app/main.py >> /var/log/cron.log 2>&1" > /app/crontab

# 将crontab文件内容写入crontab
crontab /app/crontab

# 打印crontab任务以验证
echo "[$CURRENT_TIME]Crontab Task:$(crontab -l)"

# 确保日志文件存在并具有正确的权限
touch /var/log/cron.log
chmod 644 /var/log/cron.log

# 启动cron服务
exec cron -f &
# 等待一段时间，确保cron服务已经开始运行
sleep 1

# 将cron日志输出到标准输出
tail -f /var/log/cron.log
