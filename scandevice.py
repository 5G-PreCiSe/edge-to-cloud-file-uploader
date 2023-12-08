import psutil
import time

device = "/dev/sda1"

if __name__ == "__main__":
    while True:
        found = False
        for item in psutil.disk_partitions():
            if item.device == device:
                found = True
        if found:
            print("Device ",device," is present")
        else:
            print("Device is not present")
        time.sleep(1)
        