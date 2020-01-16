# CPSC-471 FTP Server and FTP Client

## Project Overview:
The objective of this project was to develop a simple FTP server and FTP client. The application allows the client to connect to the server in order to list server files, upload to, and download from the server, both textual data, and non-textual data such as images etc. There was a focus on protocol design during development.

### Team
- Dion W. Pieterse
- Justin Chin
- Ruchi Bagwe
- Randy Baldwin

### Running the FTP Server
python3.6 server\_ftp.py \<chosen port number\>

#### Example (via console)
python3.6 server\_ftp.py 3321

### Running the FTP Client
python3.6 client\_ftp.py \<domain name of server\> \<server port number\>

**Note:** The domain name will be resolved to a 32-bit IP address via DNS Lookup.

#### Example (via console)
python3.6 client\_ftp.py 127.0.0.1 3321
