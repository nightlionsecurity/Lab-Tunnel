Automate the process of deploying virtual pen-testing boxes. 
Easily create reverse tunnel and automatically assign a machine hostname and proper reverse connection based on next available host name. 


!! TESTED WITH kali-linux and raspberry pi !!

There are two files in this package: host_client.py  host_name_flask_alch.py

* host_client.py

this file is intended to be run on clients. There is two variables to be changed:

__SERVER_IP__  and __SERVER_PORT__

__SERVER_IP__  is the ip address of ther server on which you are going to run host_name_flask_alch.py program. __SERVER_PORT__ is the port of flask web server. It is set to be 5001 on  host_name_flask_alch.py program (variable PORT). 

On client machine put this file to directory:

/usr/local/bin

Then add the following line to file /etc/rc.local before “exit 0”:

/usr/bin/python /usr/local/bin/host_client.py

Be sure ssh is running on the current run level. To enable it, execute this command:

# systemctl enable ssh

* host_name_flask_alch.py
This file is going to be run on server. If you are going to run this server with user root, you may want to change REMOTE_USER variable.
