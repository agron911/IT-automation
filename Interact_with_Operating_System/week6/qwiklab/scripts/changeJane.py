#!/usr/bin/env python3
import sys
import subprocess

oldfile = open(sys.argv[1])
for line in oldfile.readlines():
	old = line.strip()
	new = old.replace('jane','jdoe')
	subprocess.run(['mv',old,new])
oldfile.close()
