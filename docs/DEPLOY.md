# 部署与生产硬化

## 必配环境变量

| 变量 | 说明 |
|------|------|
| `DJANGO_SECRET_KEY` | 生产密钥；`DJANGO_DEBUG=0` 时缺失会拒绝启动 |
| `DJANGO_DEBUG` | 生产保持 `0`（默认值） |
| `DJANGO_ALLOWED_HOSTS` | 域名/IP 列表，逗号分隔；默认仅 localhost |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | HTTPS 站点来源，例如 `https://biotools.example.com` |
| `BIOTOOLS_API_KEYS` | 逗号分隔 API Key；非空时写接口必须带 `X-API-Key` |
| `BIOTOOLS_REQUIRE_API_KEY` | 设为 `1` 时强制要求密钥 |
| `BIOTOOLS_ANNOTATION_RATE` | 注释接口限流，默认 `30/min` |
| `BIOTOOLS_JOB_COOLDOWN_SECONDS` | 同一客户端创建任务的最小间隔，默认 `10` |
| `BIOTOOLS_JOB_STALE_AFTER_SECONDS` | worker 异常退出后，RUNNING 任务重新排队阈值，默认 `1800` |
| `ANNOVAR_PUBLIC_ENABLED` | 默认 `0`；确认 ANNOVAR 授权后再设 `1` |

先复制并修改环境文件：

```bash
cp .env.example .env
# 至少替换 DJANGO_SECRET_KEY 和 DJANGO_ALLOWED_HOSTS
```

## Web 与任务 worker

后台任务不再运行于 Gunicorn daemon thread。Compose 会启动三个角色：

- `migrate`：一次性执行数据库迁移；
- `web`：Django/Gunicorn API；
- `worker`：执行 `python manage.py run_annotation_worker`，从共享数据库领取任务。

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f worker
```

非 Compose 部署也必须单独守护 worker：

```bash
python manage.py migrate
python manage.py run_annotation_worker
```

worker 被终止时，任务会保留为 `running`；超过 `BIOTOOLS_JOB_STALE_AFTER_SECONDS` 后自动重新排队，不会永久丢失。

## 反向代理示例（Nginx）

```nginx
server {
  listen 443 ssl;
  server_name biotools.example.com;

  client_max_body_size 2m;

  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Request-ID $request_id;
    proxy_read_timeout 320s;
  }
}
```

只有在反向代理会覆盖而不是透传客户端伪造头时，才启用：

```dotenv
DJANGO_TRUST_X_FORWARDED_PROTO=1
BIOTOOLS_TRUST_X_FORWARDED_FOR=1
DJANGO_SECURE_SSL_REDIRECT=1
DJANGO_SESSION_COOKIE_SECURE=1
DJANGO_CSRF_COOKIE_SECURE=1
DJANGO_SECURE_HSTS_SECONDS=31536000
```

首次启用 HSTS 应先使用较短时间验证，确认所有子域均支持 HTTPS 后再启用 includeSubDomains/preload。

## Docker socket 安全

默认 Compose **不挂载** `/var/run/docker.sock`。Docker socket 等价于宿主机 root 权限，不应进入公开服务容器。

容器镜像内自带 VEP，因此默认 `VEP_MODE=local`。若确实需要 `VEP_MODE=docker` 或 `ANNOVAR_MODE=docker`，应通过仅用于受信环境的本地 Compose override 显式挂载 socket，并接受相应宿主机风险；不要把该挂载提交为默认生产配置。

## 鉴权调用

```bash
curl -X POST https://biotools.example.com/api/v1/annotations/ \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: YOUR_KEY' \
  -d '{"engine":"vep","assembly":"GRCh37","variants":["17:43092951 G>A"]}'
```

浏览器可在「引擎与设置」页保存 API Key 到 localStorage。注释页提交会创建后台任务（`POST /api/v1/jobs/`），并受冷却限制。

## 日志

访问日志由 `biotools.access` 输出，包含 `request_id` / method / path / status / duration_ms，**不记录变异序列正文**。任务日志由 `biotools.jobs` 和 worker 标准输出记录。

## 注释资源路径

| 用途 | 默认路径 |
|------|----------|
| 共享 SQLite 数据库 | Compose named volume `biotools-db`，容器内 `/data/db/db.sqlite3` |
| VEP cache | `data/vep`（`VEP_CACHE_DIR`） |
| ANNOVAR humandb | `data/annovar/humandb`（`ANNOVAR_DB_DIR`，含 hg19 + hg38） |

VEP GRCh38 后台下载：`BACKGROUND=1 bash scripts/download_vep_cache.sh merged GRCh38`，日志在 `data/vep/.downloads/`。脚本会在完成、失败或收到终止信号时清理 PID 文件，并在下次启动时移除失效 PID。

## Legacy 数据清理

- 可删：`legacy/online-vep/vep_data/*.tar.gz`（解压后重复包，约 24GB）
- 暂留：已解压的 `115_GRCh38` cache，直到 `VEP 116 + GRCh38` cache 下载并验收后再删整个 `legacy/online-vep/`
- FastAPI 栈已迁入 `legacy/online-tool/`，勿再作为权威入口
