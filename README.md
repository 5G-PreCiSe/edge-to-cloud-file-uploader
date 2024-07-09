# Edge to Cloud File Uploader
This repository contains the sources of a Python tool for uploading files from a local directory to an S3 storage.
This tool was originally developed to upload Drone recordings (RGB and spectral images) from a memory card to a cloud backend over a 5G wireless connection.
The memory card is inserted into a card reader connected via USB to a headless Raspberry Pi, which serves as an edge device and executes this Python tool.
As this tool is designed to run on a headless Raspberry Pi, it implements an MQTT API, enabling remote control over command messages.

## Installation
* Step 1: Download this repository and copy the downloaded content to ```/home/user/workspace/edge-to-cloud-file-uploader```
* Step 2: Add a file named ```config.ini``` to ```/home/user/workspace/edge-to-cloud-file-uploader``` (TODO: explain how to modify this file)
* Step 3: Modify ```/etc/sudoers.d``` as follows:
  - Run ```sudo visudo```
  - Add ```user    ALL=NOPASSWD: /usr/bin/mount, /usr/bin/umount, /usr/bin/shutdown, /usr/bin/reboot``` after ```%sudo   ALL=(ALL:ALL) ALL```
  - Save file
* Step 4: Create a service that starts this Python app after start-up:
  - Run ```sudo nano /lib/systemd/system/edge-to-cloud-uploader.service```
```
[Unit]
Description=Edge to Cloud Uploader
After=multi-user.target

[Service]
WorkingDirectory=/home/user/
User=user
ExecStart=/usr/bin/python3 /home/user/workspace/edge-to-cloud-file-uploader/app.py &
Type=idle

[Install]
WantedBy=multi-user.target
``` 
  - Run ```sudo chmod 644 /lib/systemd/system/edge-to-cloud-file-uploader.service```
  - Run ```sudo systemctl daemon-reload```
  - Run ```sudo systemctl enable sample.service```
  - Run ```sudo reboot```
  
## MQTT API
The *Edge to Cloud File Uploader* exposes an MQTT API that allows one to control the device remotely, in particular, to trigger essential functions like mounting a memory card, browsing the file system, and issuing an upload job.
A client can trigger these functions by issuing command messages over dedicated command topics the *Edge to Cloud File Uploader* subscribes to. The *Edge to Cloud File Uploader* executes the respective function and publishes the result over a dedicated response topic the clients can subscribe to.

The *Edge to Cloud File Uploader* subscribes to several command topics with the format `cmd/[NAME]`, each addressing one or multiple functions, e.g., `cmd/jobs`, being associated with jobs-related functions. For each command topic, there exists a response topic with the format `stat/[NAME]`, e.g., `stat/jobs`.
If a command topic addresses multiple functions, the client has to specify the exact function over an additional `command` property in the message's payload (see details below). Moreover, the client may specify a `correlationId` in the payload of the command message. The *Edge to Cloud File Uploader* embeds this `correlationId` into the response message so that the client is able to correlate both messages (see details below). 

During device registration, it is possible to overwrite several topics, i.e., change the default topic names and structures at runtime. Note that this feature is not supported for all topics.

The MQTT API is documented in [AsyncAPI.yml](https://github.com/5G-PreCiSe/edge-to-cloud-file-uploader/blob/main/AsyncAPI.yml).








 




