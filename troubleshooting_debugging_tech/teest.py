#!/usr/bin/env python3
def car_listing(car_price):
	result=''
	for car,price in car_price.items():
		result+='{} costs {} dollars '.format(car,price)+'\n'
	return result

print(car_listing({'Kia Soul':190000,'Lamborghini Diablo':5500000,'Ford':10000}))

