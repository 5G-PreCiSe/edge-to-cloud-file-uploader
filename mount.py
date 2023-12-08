import sh

if __name__ == "__main__":
    sh.sudo.mount("/dev/sdb1","/media/user","-texfat")