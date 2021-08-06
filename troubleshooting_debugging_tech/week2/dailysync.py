#!/usr/bin/env python3

from multiprocessing import Pool
import subprocess
import os

src = os.path.expanduser('~/data/prod')
dest = os.path expanduser('~/data/prod_backup')

def main(task):
	subprocess.call(['rsync','-arq',src,dest])

if __name__=="__main__":
	p = Pool(len([dir for dirs in os.listdir(src)]))
	p.map(main,os.listdir(src)
