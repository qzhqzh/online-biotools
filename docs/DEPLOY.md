# 部署与生产硬化

## 必配环境变量

| 变量 | 说明 |
|------|------|
| `DJANGO_SECRET_KEY` | 生产密钥（勿用默认值） |
| `DJANGO_DEBUG` | 生产设为 `0` |
| `DJANGO_ALLOWED_HOSTS` | 域名/IP 列表，逗号分隔 |
| `BIOTOOLS_API_KEYS` | 逗号分隔 API Key；**非空时** `POST /api/v1/annotations/` 必须带 `X-API-Key` |
| `BIOTOOLS_REQUIRE_API_KEY` | 设为 `1` 时强制要求密钥（即使 keys 列表为空也会拒绝，用于防误配） |
| `BIOTOOLS_ANNOTATION_RATE` | 注释接口限流，默认 `30/min` |
| `ANNOVAR_PUBLIC_ENABLED` | 默认 `0`；确认 ANNOVAR 授权后再设 `1` |

## 反向代理示例（Nginx）

```nginx
server {
  listen 443 ssl;
  server_name biotools.example.com;

  client_max_body_size 2m;

  location / {
    proxy_pass http://127.0.0.1:8800;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Request-ID $request_id;
    proxy_read_timeout 320s;
  }
}
```

## 鉴权调用

```bash
curl -X POST https://biotools.example.com/api/v1/annotations/ \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: YOUR_KEY' \
  -d '{"engine":"vep","assembly":"GRCh37","variants":["17:43092951 G>A"]}'
```

浏览器工具页可在「API Key」卡片中保存密钥到 localStorage。

## 日志

访问日志由 `biotools.access` 输出，包含 `request_id` / method / path / status / duration_ms，**不记录变异序列正文**。

## Legacy 数据清理

- 可删：`legacy/online-vep/vep_data/*.tar.gz`（解压后重复包，约 24GB）
- 暂留：已解压的 `115_GRCh38` cache，直到 `VEP 116 + GRCh38` cache 下载并验收后再删整个 `legacy/online-vep/`
- FastAPI 栈已迁入 `legacy/online-tool/`，勿再作为权威入口
