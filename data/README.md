# 注释资源目录（不进 Git）

```
data/
├── knowledge/                        # 基因 / MANE 知识库
│   ├── meta.json                     # 版本元数据（可进 Git）
│   ├── genes.jsonl                   # 本地生成，见 scripts/import_gene_knowledge.py
│   ├── transcript-map.json           # MANE ENST↔NM（本地生成）
│   └── raw/                          # NCBI 原始 gz
├── vep/                              # VEP_CACHE_DIR
│   ├── .downloads/                   # tar.gz + 下载日志 / pid
│   └── homo_sapiens_merged/
│       ├── 116_GRCh37/               # 可软链到 legacy cache
│       └── 116_GRCh38/               # 下载解压后出现
└── annovar/
    └── humandb/                      # ANNOVAR_DB_DIR（hg19 + hg38 同目录）
        ├── hg19_refGeneWithVer.txt
        ├── hg19_refGeneWithVerMrna.fa
        ├── hg38_refGeneWithVer.txt
        └── hg38_refGeneWithVerMrna.fa
```

## 下载

```bash
# 基因知识库（NCBI gene_info + MANE v1.5）
python scripts/import_gene_knowledge.py

# VEP 116 merged cache
BACKGROUND=1 bash scripts/download_vep_cache.sh merged GRCh38
# 进度：tail -f data/vep/.downloads/download_116_GRCh38.log
```

ANNOVAR 附加库（1000G / clinvar 等）可继续用 `annotate_variation.pl -downdb`，目标目录设为 `data/annovar/humandb`。
