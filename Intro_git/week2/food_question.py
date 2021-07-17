#!/usr/bin/env python3

counter={}

with open("favorite_foods.log",'r') as f:
	for line in f:
		item = line.strip()
		if item not in counter:
			counter[item] = 1
		else:
			counter[item] +=1
print("Select your favorite food below:")
for item in counter:
	print(item)

answer = input("which of the foods above is your favorite ? ")
answer = answer.lower()

try:
	print("{} of your friends like {} as well".format(counter[answer],answer))
except:
	print("hmm we can't find anyone who also like {}".format(answer))
