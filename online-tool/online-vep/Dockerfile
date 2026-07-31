FROM ensemblorg/ensembl-vep:release_116.0

USER root

# 安装 Python 3 和 pip
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        curl \
    && rm -rf /var/lib/apt/lists/*

# 创建虚拟环境并安装 Python 依赖
RUN python3 -m venv /opt/vep-api && \
    /opt/vep-api/bin/pip install --no-cache-dir \
        fastapi==0.115.6 \
        uvicorn==0.34.0 \
        pydantic==2.10.4

# 复制 API 代码
COPY api/ /opt/vep-api/app/

# 创建工作目录
RUN mkdir -p /data/cache /data/input && chmod 777 /data/cache /data/input

WORKDIR /opt/vep-api/app

EXPOSE 8089

# VEP 路径在官方镜像中
ENV VEP_BIN=/opt/vep/src/ensembl-vep/vep
ENV VEP_CACHE_DIR=/data/cache
ENV VEP_ASSEMBLY=GRCh37

CMD ["/opt/vep-api/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8089"]
