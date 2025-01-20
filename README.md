# hik_online_check
通过海康SDK调取前端摄像头状态，定时巡检并发送到钉钉，打包为镜像方便移植。
## 克隆仓库
```bash
git clone https://github.com/Vincentdu-cn/hik_online_check.git
```
## 生成docker镜像
```bash
docker build -t hikcheck:v0.99 .
```
## 运行
```bash
docker run -d --name hikcheck -v /home/hikcheck/hik.env:/app/.env hikcheck:v0.99
```
## 不同项目迁移
### 修改main.py中的ipstart的值，不需要可删除，重新构建镜像
### 打包镜像并上传至云盘，提取到下载链接，在setup.sh脚本中修改IMAGE_URL
```bash
docker save -o hikcheck_v0.99.tar hikcheck:v0.99
```
### 运行setup.sh脚本
```bash
bash setup.sh
```
