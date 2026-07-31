# online-biotools

在线变异注释工具。架构说明见 [ARCHITECTURE_PLAN.md](ARCHITECTURE_PLAN.md)。

## 技术栈（定版）

- 后端：Django + Django REST framework
- 启动：Docker Compose（gunicorn）
- 前端（后续阶段）：Django Template + React/Vite + **shadcn/ui** + **Monaco Editor**
- 引擎：VEP 116（已接入）；ANNOVAR（待服务化）

## 仓库说明

- **权威入口（重构中）**：仓库根目录 Django 项目（本 README 下述命令）。
- **遗留目录**（将迁完后删除）：`online-tool/online-vep/`（FastAPI）、`online-vep/`、`online-annovar/`。
- **大数据不进 Git**：`data/`、`**/cache/`、`**/vep_data/`、`**/humandb/`、`*.tar.gz`。

## 本地开发（无 VEP 二进制时仅测 API/页面）

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py test apps.annotations
python manage.py runserver 8000
```

## Docker Compose（含 VEP）

若已有遗留 GRCh37 cache，可直接挂载：

```bash
export VEP_HOST_CACHE=./online-tool/online-vep/cache
docker compose up -d --build
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
curl http://localhost:8000/api/v1/engines/
```

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
