# online-biotools

在线变异注释工具（VEP / ANNOVAR），目标形态见 [ARCHITECTURE_PLAN.md](ARCHITECTURE_PLAN.md)。

## 当前状态（初版）

- 权威重构方向：**Django + DRF + Docker Compose**；前端 **Django Template + React（Vite）+ shadcn/ui + Monaco Editor**。
- 仓库内仍保留历史实验目录（将逐步迁入 Django 后删除）：
  - `online-tool/online-vep/` — 现有 FastAPI + VEP 116（GRCh37）服务
  - `online-vep/` — 遗留 VEP 115 CLI 沙箱（仅脚本入仓，cache 不入仓）
  - `online-annovar/` — ANNOVAR CLI 沙箱（仅编排与小样例入仓，数据库不入仓）

**Reference data（cache / humandb / `*.tar.gz`）不纳入 Git**，需本地或部署卷挂载。

## 快速启动（遗留 FastAPI VEP）

```bash
cd online-tool/online-vep
bash scripts/download_cache.sh   # 首次，约 24GB GRCh37 cache
docker compose up -d --build
curl http://localhost:8093/health
```

## 安全提示

若本地曾出现 `humandb/wget-log*` 等下载日志，可能含云凭证痕迹：请**轮换相关 AccessKey**，并确保此类文件已被 `.gitignore` 排除（切勿提交）。
