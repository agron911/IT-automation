#!/usr/bin/env python3
import shutil
import sys
import os
import socket
def check_reboot():
	return os.path.exists("/run/reboot-required")

def check_disk_full(disk, min_gb,min_percent):
	"""Returns True if there isn't enough disk space"""
	du =shutil.disk_usage(disk)
	percent_free = 100*du.free/du.total
	gigabytes_free = du.free/2**30
	if percent_free < min_percent or gigabytes_free<min_gb:
		return True
	return False

def check_root_full():
		return check_disk_full(disk="/",min_gb=2,min_percent=10)

def check_no_network():
	"""Returns True if it fails to resolve google's URL"""
	try:
		socket.gethostbyname("www.google.com")
		return False
	except:
		return True

def main():
	checks=[
		(check_reboot,'pending reboot'),
		(check_root_full,'Root partition full'),
		(check_no_network,"No working network"),
	]
	for check,msg in checks:
		if check():
			print(msg)
			sys.exit(1)
	print("Everything ok.")
	sys.exit(0)
main()
