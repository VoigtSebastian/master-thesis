FROM ubuntu:24.04

ARG PYTHON=python3.10

ENV PYTHON="$PYTHON" \
    TERM=xterm-256color \
    TZ=Europe/London \
    DEBIAN_FRONTEND=noninteractive \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en

# Tools
RUN apt-get update
RUN apt-get dist-upgrade -y
RUN apt-get install -y xz-utils build-essential curl vim unzip libssl-dev pkg-config xz-utils make cmake gcc
RUN apt-get install -y bzip2 libncurses5-dev libffi-dev libreadline-dev sqlite3 libsqlite3-0 libsqlite3-dev libbz2-dev tk tk-dev lzma-dev lzma
RUN apt-get install -y ${PYTHON} python3-pip
RUN apt-get install -y fontconfig fonts-liberation
RUN apt-get install -y npm nodejs
RUN apt-get install -y liblzma-dev

RUN apt-get clean

CMD ["/usr/bin/bash"]
