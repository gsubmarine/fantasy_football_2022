from PyPDF2 import PdfReader
from pdfminer.high_level import extract_text as fallback_text_extraction
import re
from bs4 import BeautifulSoup  
import requests
import urllib3
import pandas as pd
http = urllib3.PoolManager()
import matplotlib.pyplot as plt

years = ["2018"]
filenames = ['espn_' + year + ".pdf" for year in years] 
outcomes_files = [ "yearly/" + year + ".csv" for year in years]

def pdf_to_text(filename:str) -> str:

    text = ""
    try:
        reader = PdfReader(filename)
        for page in reader.pages:
            text += page.extract_text()
            return text
    except Exception as exc:
        text = fallback_text_extraction(filename)
        print("FAIL Parsing PDF ", exc)
        return


def parse_top_rb_from_espn_cheatsheet(text: str) :
    #seperate text into a list of rows
    lines = []
    line = ""
    for char in text:
        if char == "\n":
            lines.append(line)
            line=""
            continue
        line+=char
    #Find runningback value in each row
    running_back_names = []
    ADP = []
    for line in lines:
        line_split =  line.split('.')
        #index 2 in each line is the running back column
        #'6. (79) Aaron Rodgers, GB $4 13 6. (8) Ezekiel Elliott, DAL $50 7 83. (276) Dwayne Washington, NO $0 6 73. (164) Amon-Ra St. Brown, DET $0 9'
        running_back_match = re.search(r"\) .+(?=,)", line_split[2]).group()
        running_back_names.append(running_back_match[2:])

        #parse out ADP
        ADP_match = re.search(r"\(.+(?=\))", line_split[2]).group()
        ADP.append(ADP_match[1:])
        print(ADP)
    
        if line == lines[20]:
            break
    return running_back_names, ADP

outcomes = pd.read_csv(outcomes_files[0])

df = pd.DataFrame(columns=['name', 'cheatsheet_name', 'year', 'fantasy_points'])
filename_index = -1
for filename in filenames:
    filename_index +=1
    outcomes = pd.read_csv(outcomes_files[filename_index])
    text = pdf_to_text(filename)
    rb_list, ADP = parse_top_rb_from_espn_cheatsheet(text)
    index = -1
    for rb in rb_list:
        index+=1
        stats = outcomes.loc[outcomes.Player == rb]
        if len(stats) < 1:
            print("could not find data for : ", rb)
            continue
        print(int(stats.FantasyPoints))
        newdfrow = pd.DataFrame({'name': [rb], 'cheatsheet_name': [filename], 'year': [int(2019)], 'fantasy_points': [int(stats.FantasyPoints)], 'ADP': [int(ADP[index])]})
        df = pd.concat([df,newdfrow] , ignore_index=True)


plt.figure(2)
plt.plot(df.ADP, df.fantasy_points, '.', markersize=20)