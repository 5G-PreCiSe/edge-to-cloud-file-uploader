import sh

if __name__ == "__main__":
    sh.sudo.mount("/dev/sda1","/media/user","-texfat")