#!/usr/bin/env python3

import csv
import datetime as dt
import requests

FILE_URL = "https://storage.googleapis.com/gwg-content/gic215/emploees-with-date.csv"

def get_start_date():
	print("\n Getting the first start date to query for. \n")
	print("The date must be greater than Jan 1st 2018")
	
	year = int(input('Enter a value for the year:'))
	month = int(input('Enter a value for the month: '))
	day = int(input('Enter the day:'))
	
	return dt.datetime(year,month,day)
	
def get_file_lines(url):
	response = requests.get(url, stream=True)
	lines = []
	
	for line in response.iter_lines():
		lines.append(line.decode('UTF-8'))
	return lines

def get_some_or_newer(start_data,data):
	reader = csv.reader(data[1:])
	
	min_date = dt.datetime.today()
	min_date_employees = []
	for row in reader:
		row_date = dt.datetime.strptime(row[3], '%Y-%m-%d')
		if row_date< start_date:
			continue
		if row_date <min_date:
			min_date = row_date
			min_date_employees=[]
			
		if row_date ==min_date:
			min_date_employees.append('{} {}'.format(row[0], row[1]))
	return min_date, min_date_employees

def list_newer(start_date):
	data = get_file_lines(FILE_URL)
	while start_date < dt.datetime.today():
		start_date, employees = get_some_or_newer(start_date,data)
		print("started on {}: {}".format(start_date.strftime("%b %d, %Y"),employees))
		
	start_date = start_date +dt.datetime.timedelta(days=1)
	
def main():
	start_date = get_start_date()
	list_newer(start_date)
if __name__=="__main__":
	main()


	
