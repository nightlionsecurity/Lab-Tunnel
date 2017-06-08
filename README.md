Automate the process of deploying virtual pen-testing boxes. Easily create reverse tunnel and automatically assign a machine hostname and proper reverse connection based on next available host name.

* TESTED WITH kali-linux and raspberry pi *

There are five files in this package:
1. readme.txt 
2. config.conf
3. hostserver - make this file executable
4. host_server.py - make this file executable
5. host_client.py - make this file executable

1) `readme.txt`: this help file

2) `config.conf`: this file contains configuration parameters and should be exist on both server and client. Parameters are:
**ServerIP:**  IP address of ther server on which you are going to run
**ServerPort:** Port number of web server
**SecretKey: **is any string value used as password
**RemoteUser:** the username that will do ssh to clients. If not set, username who runs the server will be used.

3) `hostserver`: this file is used to start and stop the server. Please make this file executable. To start server execute:
./ hostserver start
To stop server execute:
./ hostserver stop

4) `host_server.py`: the actual server code present in this file. Please make this file executable. To start and stop the server use `hostserver` file.

5) `host_client.py`: client configuration code present in this file. Please make this file executable. 

#Server Configuration
On server you will have these files: `hostserver`, `host_server.py`, and `config.conf`
This software is written with “zero config” philosophy. Everything is automated. The only thing you may configure is the IP address of the server. Configuration parameters are stored in simple config file: `config.conf`. Please change the **ServerIP** parameter in this file. The same `config.conf` file will be used both in server and client. In server `config.conf` file should be located where `hostserver` and `host_server.py` file present. You may also want to change **RemoteUser** parameter.

Server logs will be written to `server.log` and `server.out` files.

#Client Configuration
On client machine you will have these files: `host_client.py` and `config.conf`

Put these files (`host_client.py` and `config.conf`) under directory `/usr/local/bin` then add the following line to file `/etc/rc.local` before `exit 0`:

/usr/bin/python /usr/local/bin/host_client.py

Be sure ssh is running on the current run level. To enable it, execute this command:

systemctl enable ssh

Before booting the client, server should be started.
