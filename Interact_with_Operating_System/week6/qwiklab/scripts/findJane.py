#!/bin/bash

>oldFiles.txt

files=$(grep ' jane ' ../data/list.txt | cut -d ' ' -f3)
for file in $files;do
	if [ -e $HOME/IT-automation/Interact_with_Operating_System/week6/qwiklab$file ];then echo $HOME/IT-automation/Interact_with_Operating_System/week6/qwiklab$file>>oldFiles.txt;fi
done
