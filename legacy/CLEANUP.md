# Legacy 清理记录

## 已执行（低风险）
- 删除 `online-vep/vep_data/homo_sapiens_vep_115_GRCh38.tar.gz`（与解压目录重复，约 24GB）
- 删除未引用的 `Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz`（若存在）

## 待确认后再删
- 整个 `legacy/online-vep/`：需先完成 VEP 116 GRCh38 cache 下载与验收
- `legacy/online-tool/` FastAPI：确认无外部仍依赖 8093 后删除

## ANNOVAR 授权
- 在线服务默认 `ANNOVAR_PUBLIC_ENABLED=0`
- 确认商业/再分发条款后再开启
