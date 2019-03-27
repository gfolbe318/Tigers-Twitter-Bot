from bs4 import BeautifulSoup
from urllib.request import urlopen
import pandas as pd
import datetime

# Converts a month to a number
month_to_number = {
    "Mar" : "03",
    "Apr" : "04",
    "May" : "05",
    "Jun" : "06",
    "Jul" : "07",
    "Aug" : "08",
    "Sep" : "09",
    "Oct" : "10",
    "Nov" : "11"
}

# Converts a number to a month
number_to_month = {
    "03" : "Mar",
    "04" : "Apr",
    "05" : "May",
    "06" : "Jun",
    "07" : "Jul",
    "08" : "Aug",
    "09" : "Sep",
    "10" : "Oct",
    "11" : "Nov"
}

# Days in each month Used to deal with special case of a game being on the last
# day of a month A tweet on May 1st would actually refer to a game being played
# on April 30th 
days_in_month = {
    "Mar" : "31",
    "Apr" : "30",
    "May" : "31",
    "Jun" : "30",
    "Jul" : "31",
    "Aug" : "31",
    "Sep" : "30",
    "Oct" : "31",
    "Nov" : "30",
}

# List of months for indexing purposes
month_list = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun", 
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]

# Used to tell the place of the Tigers
nth = {
    0 : "first",
    1 : "second",
    2 : "third",
    3 : "fourth",
    4 : "last"
}

# Maps acronym to team name
MLB_teams = {
    #AL EAST#
    "BAL" : "Orioles", "BOS" : "Red Sox", "NYY" : "Yankees", 
    "TBR" : "Rays", "TOR" : "Blue Jays",

    #AL CENTRAL#
    "CHW" : "White Sox", "CLE" : "Indians", 
    "KCR" : "Royals", "MIN" : "Twins",

    #AL WEST#
    "SEA" : "Mariners", "HOU" : "Astros", "LAA" : "Angels", 
    "TEX" : "Rangers", "OAK" : "Athletics",

    #NL EAST#
    "ATL" : "Braves", "MIA" : "Marlins", "NYM" : "Mets",
    "PHI" : "Phillies", "WSN" : "Nationals",

    #NL CENTRAL#
    "CHC" : "Cubs", "CIN" : "Reds", "MIL" : "Brewers",
    "PIT" : "Pirates", "STL" : "Cardinals",

    #NL WEST#
    "ARI" : "Diamondbacks", "COL" : "Rockies", "LAD" : "Dodgers",
    "SDP" : "Padres", "SFG" : "Giants"
}

def get_day_before(date):
    orig_month, orig_day = date.split(" ")
    new_day = ""
    new_month = ""

    # If the game was in the middle of the month, we can just subtract one day
    # to get the correct one
    if int(orig_day) != 1:
        new_day = str(int(orig_day) - 1)
        new_month = orig_month
    
    # Otherwise, we must do some mapping/arithmetic to get the correct date
    # string
    else:
        new_month = month_list[int(month_to_number[orig_month]) - 2]
        new_day = days_in_month[new_month]
    
    return new_month + " " + new_day

# This section of code is used to scrape the homepage of baseball reference and
# find out the current standings of the AL Central. 
homepage_link = "https://www.baseball-reference.com/"
link_soup = BeautifulSoup(urlopen(homepage_link), "lxml")
standings = link_soup.find_all("table")
AL_standings_df = pd.read_html(str(standings))[0]

# Who is leading the division?
division_leader = AL_standings_df.at[7, "AL"]

# If the leader is Detroit, find out how many games they are up by, and who is
# in second place
if division_leader == "DET":
    second_place = AL_standings_df.at[8, "AL"]
    games_back = str(AL_standings_df.at[8, "GB"])

# If the Tigers are not leading the division, who is? How many games back are
# the Tigers?
else:
    tigers_row = AL_standings_df.loc[AL_standings_df['AL'] == "DET"].index[0]
    games_back = str(AL_standings_df.at[tigers_row, 'GB'])

# Map the position of the tigers to an appropriate place.
place = nth[tigers_row - 7]

# This next section of code will get us the current date and create a key to
# look into the Tigers's schedule
date = str(datetime.datetime.now()).split(" ")[0]
year, month, day = date.split("-")
key = number_to_month[month] + " " + str(day)
key = get_day_before(key)

# Scrapes schedule
schedule_link = "https://www.baseball-reference.com/teams/DET/2018-schedule-scores.shtml"
schedule_soup = BeautifulSoup(urlopen(schedule_link), "lxml")
schedule_table = schedule_soup.find("table")

#Index into the first element in the list. I don't know exactly why the "find"
# function was returning as a list, but indexing into it fixed the issue.
schedule_df = pd.read_html(str(schedule_table))[0]

#Get all the games played on the specifc day. We expect this number to be 0 (no
# game played), 1 (a game was played), or 2 (a double-header was played)
games_on_date = schedule_df[schedule_df["Date"].str.contains(key)]
num_games = games_on_date.shape[0]
