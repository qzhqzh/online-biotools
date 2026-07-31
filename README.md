# online-biotools

在线变异注释工具。架构说明见 [ARCHITECTURE_PLAN.md](ARCHITECTURE_PLAN.md)。

## 技术栈（定版）

- 后端：Django + Django REST framework
- 启动：Docker Compose（gunicorn）
- 前端：Django Template + React/Vite + **shadcn/ui** + **Monaco Editor**（`frontend/`）
- 引擎：VEP 116（已接入）；ANNOVAR（待服务化）

## 本地开发

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py test apps.annotations

# 前端（首次）
cd frontend && npm install && npm run build && cd ..

python manage.py runserver 8000
# 打开 http://127.0.0.1:8000/tools/annotate/
```

前端热更新（可选）：另开终端 `cd frontend && npm run dev`（已代理 `/api` 到 8000）。

## Docker Compose（含 VEP）

若已有遗留 GRCh37 cache，可直接挂载：

```bash
export VEP_HOST_CACHE=./online-tool/online-vep/cache
docker compose up -d --build
curl http://localhost:8000/health/live
curl http://localhost:8000/api/v1/engines/
```

打开 http://localhost:8000/tools/annotate/ 使用 shadcn + Monaco 工具页。

或下载到 `./data/vep`：

```bash
bash scripts/download_vep_cache.sh merged GRCh37
docker compose up -d --build
```

### 注释示例

```bash
curl -s -X POST http://localhost:8000/api/v1/annotations/ \
  -H 'Content-Type: application/json' \
  -d '{"engine":"vep","assembly":"GRCh37","variants":["17:43092951 G>A"]}'
```

无对应 assembly cache 时返回 **503**（不再假装支持）。

## 安全提示

本地若曾有 `wget-log*` 含云凭证，请轮换 AccessKey；此类文件已被 `.gitignore` 排除。
