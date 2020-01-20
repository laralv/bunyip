import csv
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", help="csv", action="store")
args = parser.parse_args()
input_csv = args.input
files = []
with open(input_csv, newline='\n') as csvfile:
    for row in csv.reader(csvfile):
        files.append(row)
for file in files:
    print(file)
#print(len(files))
