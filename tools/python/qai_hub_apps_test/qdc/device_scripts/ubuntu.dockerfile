ARG REGISTRY_PREFIX=""
ARG INSTALL_QUALCOMM_CA="false"

FROM ${REGISTRY_PREFIX}ubuntu:24.04

ARG INSTALL_QUALCOMM_CA="false"

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN if [ "$INSTALL_QUALCOMM_CA" = "true" ]; then \
        mkdir -p /usr/local/share/ca-certificates/qualcomm.com \
        && wget --no-check-certificate -P /usr/local/share/ca-certificates/qualcomm.com \
            https://pki.qualcomm.com/qc_root_g2_cert.crt \
            https://pki.qualcomm.com/ssl_v2_cert.crt \
            https://pki.qualcomm.com/ssl_v4_cert.crt \
        && update-ca-certificates \
        && wget --no-check-certificate \
            -O /usr/local/share/ca-certificates/qualcomm.com/nscacert.crt \
            https://github.qualcomm.com/raw/netskope-ssl/download/main/nscacert.cer \
        && update-ca-certificates; \
    fi

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    software-properties-common \
    sudo \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app

RUN if [ "$INSTALL_QUALCOMM_CA" = "true" ]; then \
        export SSL_CERT_FILE=/usr/local/share/ca-certificates/qualcomm.com/nscacert.crt; \
        export REQUESTS_CA_BUNDLE=/usr/local/share/ca-certificates/qualcomm.com/nscacert.crt; \
    fi \
    && if [ -f install_runtime.sh ]; then QAIRT_INSTALL_SKIP=true bash install_runtime.sh; fi

ENTRYPOINT ["bash", "-c", "source /app/scripts/qairt_utils.sh && install_qairt && exec \"$@\"", "--"]
CMD ["bash"]
