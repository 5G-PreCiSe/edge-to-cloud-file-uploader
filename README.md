# Edge to Cloud File Uploader
This repository contains the sources of a Python tool for uploading files from a local directory to an S3 storage.
This tool was initially developed to upload Drone recordings (RGB and spectral images) from a memory card to a cloud backend over a 5G wireless connection.
The memory card is inserted into a card reader connected via USB to a headless Raspberry Pi, which serves as an edge device and executes this Python tool.
This tool is designed to run on a headless Raspberry Pi. It implements an MQTT API, enabling remote control over command messages.

## Hardware Requirements
To run the Edge-to-Cloud File Uploader, the following hardware is required:
- Raspberry Pi 4 Model B
- 5G PreCiSe Edge-to-Cloud File Uploader HAT
- USB Card Reader

## Installation
After the installation of Raspberry Pi OS (we recommend to install Bookworm 64 bit), go through the following steps to the install the Edge-to-Cloud File Uploader software:
* Step 1: Run the following commands to download this repository and copy the downloaded content to ```/home/user/workspace/edge-to-cloud-file-uploader```:
  ```
  cd ~
  mkdir workspace
  git clone
  https://github.com/5G-PreCiSe/edge-to-cloud-file-uploader
  ```
* Step 2: Install required Python libraries listed in ```requirements.txt```:
  ```
  pip install -r ./edge-to-cloud-file-uploader/requirements.txt --break-system-packages
  ```
  Additionally, ```RPi.GPIO``` must be replaced by ```lgpio```. Run the following commands:
  ```
  sudo apt remove python3-rpi.gpio
  sudo apt update
  sudo apt install python3-rpi-lgpio
  ```
* Step 3: Modify ```/etc/sudoers.d``` as follows:
  - Run ```sudo visudo```
  - Add ```user    ALL=NOPASSWD: /usr/bin/mount, /usr/bin/umount, /usr/bin/shutdown, /usr/bin/reboot``` after ```%sudo   ALL=(ALL:ALL) ALL```
  - Save file
* Step 4: Make sure that the I2C interface is enabled: Run ```sudo raspi-config``` and navigate to ```3 Interface Option```. Open ```I5 I2C``` and select ```<Yes>```.
* Step 5: When the Edge-to-Cloud File Uploader starts, it loads a file named ```config.ini```, which contains the individual runtime configuration. This file contains parameters like credentials, connection strings, and MQTT topics for communication with the backend. The downloaded repository contains a template named ```config.ini_```. Rename this file to ```config.ini``` and edit the configuration parameters. In detail, run the following commands:
  ```
  cd ~/workspace/edge-to-cloud-file-uploader
  mv config.ini_ config.ini
  nano config.ini
  ```
  Set the ```AccessKey```, the ```SecretKey```, and the ```Server``` address of S3 storage. Moreover, specify ```Address```, ```Port```, ```Username``` and ```Password``` or your MQTT broker.
* Step 6: Finally, create a service that starts this Python app after start-up:
  - Run ```sudo nano /lib/systemd/system/edge-to-cloud-file-uploader.service``` and paste the following lines into the service definition file:
```
[Unit]
Description=Edge to Cloud Uploader
Wants=network-online.target
After=multi-user.target network-online.target

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
  - Run ```sudo systemctl enable edge-to-cloud-file-uploader.service```
  - Run ```sudo reboot```
  
## MQTT API
The *Edge to Cloud File Uploader* exposes an MQTT API that allows one to control the device remotely, in particular, to trigger essential functions like mounting a memory card, browsing the file system, and issuing an upload job.
A client can trigger these functions by issuing command messages over dedicated command topics the *Edge to Cloud File Uploader* subscribes to. The *Edge to Cloud File Uploader* executes the respective function and publishes the result over a dedicated response topic the clients can subscribe to.

The *Edge to Cloud File Uploader* subscribes to several command topics with the format `cmd/[NAME]`, each addressing one or multiple functions, e.g., `cmd/jobs`, being associated with jobs-related functions. For each command topic, there exists a response topic with the format `stat/[NAME]`, e.g., `stat/jobs`.
If a command topic addresses multiple functions, the client has to specify the exact function over an additional `command` property in the message's payload (see details below). Moreover, the client may specify a `correlationId` in the payload of the command message. The *Edge to Cloud File Uploader* embeds this `correlationId` into the response message so that the client is able to correlate both messages (see details below). 

During device registration, it is possible to overwrite several topics, i.e., change the default topic names and structures at runtime. Note that this feature is not supported for all topics.

The MQTT API is documented in [AsyncAPI.yml](https://github.com/5G-PreCiSe/edge-to-cloud-file-uploader/blob/main/AsyncAPI.yml).








 




