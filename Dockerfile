# 使用官方Python基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置时区
ENV TZ=Asia/Shanghai

# 将当前目录下的所有文件复制到容器的工作目录中
COPY . /app

# 安装cron和依赖
RUN apt-get update && \
    apt-get install -y cron && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r requirements.txt

# 设置entrypoint脚本为可执行
RUN chmod +x /app/entrypoint.sh

# 启动cron服务
ENTRYPOINT ["/app/entrypoint.sh"]
