from PyPDF2 import PdfReader
from pdfminer.high_level import extract_text as fallback_text_extraction
import re
from bs4 import BeautifulSoup  
import requests
import urllib3
import pandas
http = urllib3.PoolManager()

filename = "espn_2021_cheet_sheet.pdf"
text = ""
try:
    reader = PdfReader(filename)
    for page in reader.pages:
        text += page.extract_text()
except Exception as exc:
    text = fallback_text_extraction(filename)


print(text)
lines = []
line = ""
for char in text:
    if char == "\n":
        lines.append(line)
        line=""
        continue
    line+=char

running_back_names = []
for line in lines:
    line_split =  line.split('.')
    #index 2 in each line is the running back column
    #'6. (79) Aaron Rodgers, GB $4 13 6. (8) Ezekiel Elliott, DAL $50 7 83. (276) Dwayne Washington, NO $0 6 73. (164) Amon-Ra St. Brown, DET $0 9'
    running_back_match = re.search(r"\) .+(?=,)", line_split[2]).group()
    running_back_names.append(running_back_match[2:])
    if line == lines[4]:
        break

#get info from nfl.com
for name in running_back_names:
    print(name)
    first_last_name = name.replace(" ", "-")
    print(first_last_name)
    url = "https://www.nfl.com/players/" + first_last_name + "/stats/career"

    #get player data from nfl.com
    r = http.request('GET', url)
    if r.status != 200:
        print("ERROR", url, r.status)
    else:
        soup = BeautifulSoup(r.data, 'html.parser')

    table = soup.find('table')

    for row in table.tbody.find_all('tr'):
        # Find all data for each column
        row_values = row.find_all('td')
        GP = row_values[2].text
        year = row_values[0].text
        attempts = row_values[3].text
        print(GP, year, attempts)

