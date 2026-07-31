# 注释对照知识库

用于 VEP（Ensembl / ENST）与 ANNOVAR（RefSeq / NM）结果对比。

## 导入（必做）

```bash
python scripts/import_gene_knowledge.py
# 或仅用已下载 raw：
python scripts/import_gene_knowledge.py --skip-download
# 强制重下 MANE：
python scripts/import_gene_knowledge.py --force-mane
```

生成：

| 文件 | 说明 | 是否进 Git |
|------|------|------------|
| `meta.json` | 版本、条数、MANE 说明 | 是 |
| `genes.jsonl` | NCBI 人类基因（约 19 万行） | 否（本地生成） |
| `transcript-map.json` | MANE ENST↔NM | 否（本地生成） |
| `raw/` | 原始 gz | 否 |

## MANE 版本要点

| 维度 | 说明 |
|------|------|
| 组装 | **仅 GRCh38**，无官方 GRCh37/hg19 MANE |
| 集合 | MANE Select（每基因一条常用）/ MANE Plus Clinical（临床额外） |
| 发布版 | 如 v1.5；随 NCBI `current/` 与 `README_versions.txt` 更新 |

门户「基因知识库」页顶部有同样说明与外链。

## API

- `GET /api/v1/knowledge/meta/`
- `GET /api/v1/knowledge/genes/?q=&type=protein-coding&limit=50`
- `GET /api/v1/knowledge/transcripts/?q=&mane_only=1`

## 权威来源

- https://www.ncbi.nlm.nih.gov/refseq/MANE/
- https://ftp.ncbi.nlm.nih.gov/refseq/MANE/MANE_human/current/
- https://ftp.ncbi.nlm.nih.gov/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz
- https://www.ensembl.org/info/genome/genebuild/mane.html
