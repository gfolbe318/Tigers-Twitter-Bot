from bs4 import BeautifulSoup
from urllib.request import urlopen
import pandas as pd
import datetime
import tweepy
import inflect
from time import sleep

from credentials import *
p = inflect.engine()

# Access and authorize Twitter credentials
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

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
    0 : "1st",
    1 : "2nd",
    2 : "3rd",
    3 : "4th",
    4 : "5th"
}

win_loss_single = {
    "W" : "beat the",
    "W-wo" : "beat the",
    "L" : "lost to the",
    "L-wo" : "lost to the"
}

win_loss_double = {
    "W" : "won",
    "W-wo" : "won",
    "L" : "lost",
    "L-wo" : "lost" 
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

def print_score(runs_scored, runs_allowed):
    if runs_scored > runs_allowed:
        return runs_scored + "-" + runs_allowed
    else:
        return runs_allowed + "-" + runs_scored

def get_result_no_game():
    return "The Tigers did not play yesterday"

def get_standings(standings):
    games_back = ""
    position = ""
    other_team = ""
    tied_with = ""

    # Find out what row the tigers are in
    tigers_row = standings.loc[standings['AL'] == "DET"].index[0]

    # If they are in first place, we find how many teams they are tied with
    if tigers_row == 0 or standings.at[tigers_row, "GB"] == "--":
        num_teams_tied = 0
        for i in range(0, 5):
            if standings.at[i, "GB"] == "--":
                num_teams_tied += 1
            else:
                break

        # If they are tied with one team (themselves), they are leading the
        # division outright
        if num_teams_tied == 1:
            games_back = standings.at[1, "GB"]
            
            # Avoid printing "X.0 games" (unnecessary decimals)
            full_games = games_back.split(".")
            if full_games[1] == "0":
                games_back = full_games[0]

            return (
                "They are first in the AL Central with a " + 
                games_back + " lead.\n"
            )

        # If they are tied with one other team, find out who the other team 
        # is by looking at the other row
        elif num_teams_tied == 2:
            if tigers_row == 0:
                other_team = standings.at[1, "AL"]
            else:
                other_team = standings.at[0, "AL"]
            return(
                "They are tied for first in the AL Central with the " 
                + MLB_teams[other_team] + ".\n"
            )

        # Otherwise, there is a multiple team tie for first.
        elif num_teams_tied > 2:
            return(
                "They are in a " + num_teams_tied + 
                "-way tie for first in the AL Central.\n"
            )
    
    # If the Tigers aren't in first, where are they?
    else:
        position = p.ordinal(tigers_row + 1)
        games_back = standings.at[tigers_row, "GB"]

        # Avoid printing "X.0 games" (unnecessary decimals)
        full_games = games_back.split(".")
        if full_games[1] == "0":
            games_back = full_games[0]

        # Stupid syntax to add an s if games_back == "1"
        do_I_need_an_s = "s" if games_back != "1" else "" 
 
        return(
            "They are in " + position + " place in the AL Central, " +
            "trailing by " + games_back + " game" + do_I_need_an_s + ".\n"
        ) 

def get_record(record, streak):
    typeStreak = "winning"
    if streak.find('-') != -1:
        typeStreak = "losing"

    num = str(len(streak))
    english_length = p.number_to_words(num)

    helper = p.a(english_length)
    correctUsage = helper.split(" ")[0]

    dummy_string = (
        "Their current record is " + record + ", and they are on " +
        correctUsage + " " + num + " game " + typeStreak + " streak."
    )

    return dummy_string


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
AL_Central_Standings = AL_standings_df[7:12].reset_index(drop = True)

# This next section of code will get us the current date and create a key to
# look into the Tigers's schedule
date = str(datetime.datetime.now()).split(" ")[0]
year, month, day = date.split("-")
key = number_to_month[month] + " " + str(day)
key = get_day_before(key)

# Scrapes schedule
schedule_link = "https://www.baseball-reference.com/teams/DET/" + year + "-schedule-scores.shtml"
schedule_soup = BeautifulSoup(urlopen(schedule_link), "lxml")
schedule_table = schedule_soup.find("table")

# Index into the first element in the list. I don't know exactly why the "find"
# function was returning as a list, but indexing into it fixed the issue.
schedule_df = pd.read_html(str(schedule_table))[0]

# Get all the games played on the specifc day. We expect this number to be 0 (no
# game played), 1 (a game was played), or 2 (a double-header was played)
games_on_date = schedule_df[schedule_df["Date"].str.contains(key)]
games_on_date = games_on_date.reset_index(drop = True)
num_games = games_on_date.shape[0]

game = {}
game["result"] = games_on_date.at[0, "W/L"]
game["opponent"] = games_on_date.at[0, "Opp"]
game["runs-scored"] = games_on_date.at[0, "R"]
game["runs-allowed"] = games_on_date.at[0, "RA"]

record = games_on_date.at[0, "W-L"]
streak = games_on_date.at[0, "Streak"]

game2 = {}
if num_games == 2:
    game2["result"] = games_on_date.at[1, "W/L"]
    game2["opponent"] = games_on_date.at[1, "Opp"]
    game2["runs-scored"] = games_on_date.at[1, "R"]
    game2["runs-allowed"] = games_on_date.at[1, "RA"]
    
    record = games_on_date.at[1, "W-L"]
    streak = games_on_date.at[1, "Streak"]




# We must now create a string of what will be tweeted
result_line = ""


standings_line = get_standings(AL_Central_Standings)
print(standings_line)


streak_line = get_record(record, streak)
