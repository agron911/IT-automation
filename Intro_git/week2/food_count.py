#!/usr/bin/env python3
counter={}
with open('favorite_foods.log') as f:
	for i in f:
		i = i[:-1]
		if i not in counter:
			counter[i]=1
		else:
			counter[i]+=1

sorted_food = sorted(counter.items(),key=lambda x:x[1],reverse=True)

for i in range(len(sorted_food)):
	print("{} {}".format(sorted_food[i][0],sorted_food[i][1]))
