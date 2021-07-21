#!/usr/bin/env python3

def find_item(lis,item):
	lis.sort()
	if len(lis)==0:
		return False
	middle = len(lis)//2

	if lis[middle]==item:
		return True

	if item < lis[middle]:
		return find_item(lis[:middle],item)
	return find_item(lis[middle+1:],item)
list_of_names = ["Parker","Drew","Cameron","Logan","Alex"]

print(find_item(list_of_names,'Alex'))
