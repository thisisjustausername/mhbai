# Installation of Python3.14
In order to install python3.14, run following commands: 
1. sudo apt update
2. sudo apt install -y build-essential libssl-dev zlib1g-dev libncurses5-dev libncursesw5-dev libreadline-dev libsqlite3-dev libgdbm-dev libdb5.3-dev libbz2-dev libexpat1-dev liblzma-dev libffi-dev uuid-dev wget
3. wget https://www.python.org/ftp/python/3.14.0/Python-3.14.0.tgz
4. tar -xf Python-3.14.0.tgz
5. cd Python-3.14.0
6. ./configure --enable-optimizations
7. make -j$(nproc)
8. sudo make altinstall
