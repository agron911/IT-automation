#!/usr/bin/env python3

def linear_search(list,key):
	steps = 0
	for i in range(len(list)):
		steps+=1
		if list[i] == key:
			return steps
def linear_search2(list,key):
	steps = 0
	for i,item in enumerate(list):
		steps+=1
		if item ==key:
			break
	return steps

def binary_search(list,key):
	list.sort()
	steps =1
	left = 0
	right = len(list)-1
	while left<=right:
		steps+=1
		middle = (left+right)//2

		if list[middle] == key:
			break
		if list[middle]>key:
			right = middle -1
		if list[middle]<key:
			left = middle +1
	return steps

def best_search(list,key):
	steps_linear = linear_search(list,key)
	steps_linear2= linear_search2(list,key)
	steps_binary = binary_search(list,key)
	results = 'Linear: '+str(steps_linear) +' Linear2: '+ str(steps_linear2) +' Binary: '+str(steps_binary)
	final ={'steps_linear':steps_linear,'steps_linear2':steps_linear2,'binary_search':steps_binary}
	best = max(final,key = final.get)
	return str(best)+' is the best ' + results

print(best_search([10,2,9,1,7,5,3,4,6,8],1))

