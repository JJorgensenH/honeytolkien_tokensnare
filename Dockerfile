FROM python:3.14-slim AS base

ARG USER_ID=1000

WORKDIR /app

RUN apt-get update

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY templates templates
COPY assets assets
COPY generators generators
COPY binary_template/template_linux binary_template/template_linux
COPY binary_template/template_win.exe binary_template/template_win.exe
COPY tokensnare_cli.py .
COPY tokensnare_server.py .

# Crear usuario no root
RUN useradd -u ${USER_ID} -ms /bin/bash tokensnare

RUN mkdir -p /app/honeyTokens && \
    chown -R tokensnare:tokensnare /app

USER tokensnare

CMD ["python", "tokensnare_server.py", "--host", "0.0.0.0"]
