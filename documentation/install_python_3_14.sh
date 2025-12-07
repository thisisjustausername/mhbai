#!/bin/bash

# update
sudo apt update

# install necessary libraries
sudo apt install -y build-essential libssl-dev zlib1g-dev libncurses5-dev libncursesw5-dev libreadline-dev libsqlite3-dev libgdbm-dev libdb5.3-dev libbz2-dev libexpat1-dev liblzma-dev libffi-dev uuid-dev wget

# get tgz file
wget https://www.python.org/ftp/python/3.14.0/Python-3.14.0.tgz

# install python3.14
tar -xf Python-3.14.0.tgz

# go to new directory
cd Python-3.14.0

# enable optimizations
./configure --enable-optimizations

make -j$(nproc)

# use it as additional python
sudo make altinstall
