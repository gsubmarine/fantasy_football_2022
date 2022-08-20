from PyPDF2 import PdfReader
from pdfminer.high_level import extract_text as fallback_text_extraction
import re
from bs4 import BeautifulSoup  
import requests
import urllib3
import pandas as pd
http = urllib3.PoolManager()
import matplotlib.pyplot as plt

filenames = ["espn_2018.pdf","espn_2019.pdf","espn_2020.pdf","espn_2021.pdf"] 



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


def parse_top_rb_from_espn_cheatsheet(text: str) -> list:
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
    for line in lines:
        line_split =  line.split('.')
        #index 2 in each line is the running back column
        #'6. (79) Aaron Rodgers, GB $4 13 6. (8) Ezekiel Elliott, DAL $50 7 83. (276) Dwayne Washington, NO $0 6 73. (164) Amon-Ra St. Brown, DET $0 9'
        running_back_match = re.search(r"\) .+(?=,)", line_split[2]).group()
        running_back_names.append(running_back_match[2:])
        if line == lines[4]:
            break
    return running_back_names

def rbname_to_nflprofile(name: str) -> str:
    #get info from nfl.com
    first_last_name = name.replace(" ", "-")
    first_last_name = first_last_name.replace("'", "-")
    url = "https://www.nfl.com/players/" + first_last_name + "/stats/career"
    print(name, url)

    #get player data from nfl.com
    r = http.request('GET', url)
    if r.status != 200:
        print("ERROR", url, r.status)
        return -1
    else:
        soup = BeautifulSoup(r.data, 'html.parser')
    return soup

def nflprofile_to_stats(soup: str,name: str, filename: str) -> pd.DataFrame:
    player_dict = {}
    _df = pd.DataFrame(columns=['name', 'cheatsheet_name', 'year', 'games_played', 'attempts'])

    table = soup.find('table')
    try:
        for row in table.tbody.find_all('tr'):
            # Find all data for each column
            row_values = row.find_all('td')
            games_played = row_values[2].text
            year = row_values[0].text
            attempts = row_values[3].text
            player_dict[year] = (games_played, attempts)
            print(games_played, year, attempts)
            if len(_df) == 0:
                _df = pd.DataFrame({'name': [name], 'cheatsheet_name': [filename], 'year': [int(year)], 'games_played': [int(games_played)], 'attempts': [int(attempts)]})
            else:
                newdfrow = pd.DataFrame({'name': [name], 'cheatsheet_name': [filename], 'year': [int(year)], 'games_played': [int(games_played)], 'attempts': [int(attempts)]})
                _df = pd.concat([_df,newdfrow] , ignore_index=True)
            print(len(_df))
    except Exception as exc:
        print("Skipping.Cannot parse html. Exception:  ",exc)
    return _df

player_names = []
df = pd.DataFrame(columns=['name', 'cheatsheet_name', 'year', 'games_played', 'attempts'])
for filename in filenames:
    text = pdf_to_text(filename)
    rb_list = parse_top_rb_from_espn_cheatsheet(text)
    for rb in rb_list:
        if rb in player_names:
            continue
        player_names.append(rb)
        soup = rbname_to_nflprofile(rb)
        if soup == -1:
            continue
        _df = nflprofile_to_stats(soup,rb, filename)
        if len(_df) != 0:
            df = pd.concat([df, _df], ignore_index=True)
            print(len(df))
    
