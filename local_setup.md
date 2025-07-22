# Setup for efficiently using the prototype
It is advised to use a local machine and a remote machine. 

## Remote machine
- Set up a venv and link it with Github / clone the project.
- Download all pdfs to the pdfs folder (because of size these are not on Github)

## Local machine
- Set up venv and link it with Github / clone the project.
- Connect to remote machine via ssh
- for testing server.py
  - forward port to remote machine using ssh -L 5000:127.0.0.1:5000 username@host
  - run server.py on remote machine