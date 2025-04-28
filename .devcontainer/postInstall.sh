#!/bin/bash

# Install monaspace fonts
cd /tmp
curl -LO https://github.com/githubnext/monaspace/releases/download/v1.101/monaspace-v1.101.zip \
    && unzip monaspace-v1.101.zip \
    && cd monaspace-v1.101 \
    && ./util/install_linux.sh \
    && rm -rf monaspace-v1.101.zip monaspace-v1.101 __MACOSX \
    && fc-cache -f -v

# Install typst
cd /tmp
curl -L https://github.com/typst/typst/releases/latest/download/typst-x86_64-unknown-linux-musl.tar.xz --output typst-x86_64-unknown-linux-musl.tar.xz \
    && tar xf typst-x86_64-unknown-linux-musl.tar.xz \
    && cd typst-x86_64-unknown-linux-musl/ \
    && mkdir -p ~/.local/bin \
    && cp typst ~/.local/bin

# Install pyenv
curl https://pyenv.run | bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
source ~/.bashrc

# Install Python 3.12 using pyenv
~/.pyenv/bin/pyenv install 3.12
~/.pyenv/bin/pyenv global 3.12
