#!/usr/bin/env python3

def binary_search(list,key):
	list.sort()
	left = 0
	right = len(list)-1

	while left<=right:
		middle = (left+right)//2
		if list[middle] == key:
			return middle
		if list[middle]<key:
			left = middle+1
			print('Checking the right side')
		if list[middle]>key:
			right = middle-1
			print("checking the left side")
	return -1

print(binary_search([10,9,8,6,5,4,3,2,1],1))
