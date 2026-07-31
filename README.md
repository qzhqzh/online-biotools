# online-biotools

在线变异注释工具。架构说明见 [ARCHITECTURE_PLAN.md](ARCHITECTURE_PLAN.md)。

## 技术栈（定版）

- 后端：Django + Django REST framework
- 启动：Docker Compose（gunicorn）
- 前端：Django Template + React/Vite + **shadcn/ui** + **Monaco Editor**（`frontend/`）
- 引擎：VEP 116；ANNOVAR（本地 perl 或 docker CLI）

## 目录约定

- **权威代码**：根目录 Django / `frontend/` / `scripts/`
- **遗留实验**：[`legacy/`](legacy/README.md)（FastAPI/CLI 沙箱，勿继续扩展）
- **数据不进 Git**：统一放在 `data/`（见 [`data/README.md`](data/README.md)）

```
data/vep/                              # VEP_CACHE_DIR
data/annovar/humandb/                  # ANNOVAR_DB_DIR（hg19 + hg38）
```

已有 legacy GRCh37 cache 时可软链：

```bash
mkdir -p data/vep/homo_sapiens_merged
ln -sfn "$(pwd)/legacy/online-tool/online-vep/cache/homo_sapiens_merged/116_GRCh37" \
  data/vep/homo_sapiens_merged/116_GRCh37
```

VEP GRCh38：

```bash
BACKGROUND=1 bash scripts/download_vep_cache.sh merged GRCh38
```

## 本地开发

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py test apps.annotations

cd frontend && npm install && npm run build && cd ..
python manage.py runserver 8000
# http://127.0.0.1:8000/tools/annotate/
```

ANNOVAR（宿主机）：需 docker 与镜像，或设置 `ANNOVAR_MODE=local` 指向本机 `table_annovar.pl`。

## Docker Compose

```bash
# 默认挂载 data/vep 与 data/annovar/humandb
docker compose up -d --build
curl http://localhost:8000/health/ready
curl http://localhost:8000/api/v1/engines/
```

```bash
curl -s -X POST http://localhost:8000/api/v1/annotations/ \
  -H 'Content-Type: application/json' \
  -d '{"engine":"vep","assembly":"GRCh37","variants":["17:43092951 G>A"]}'
```

无对应 cache/db 时返回 **503**。

## 安全提示

勿提交 `wget-log*` / AccessKey；大数据目录已在 `.gitignore`。  
生产请配置 `BIOTOOLS_API_KEYS`，详见 [docs/DEPLOY.md](docs/DEPLOY.md)。  
ANNOVAR 默认关闭（`ANNOVAR_PUBLIC_ENABLED=0`），授权确认后再开启。
