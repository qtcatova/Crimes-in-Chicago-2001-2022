import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re


def clean_data(df):
    
    # Case Number - little nulls
    df = df.dropna(subset=['Case Number'])

    df = df.drop(columns=['X Coordinate','Y Coordinate','Updated On'])
    
    #Location
    df['Location Description'] = df['Location Description'].fillna("UNKNOWN")
    
    #The police District
    df['District'] = df['District'].fillna(df['District'].median())
    df['Ward'] = df['Ward'].fillna(df['Ward'].median())
    df['Community Area'] = df['Community Area'].fillna(df['Community Area'].median())
    
    ## 86848/ 7784664 = 0.001*100=1,1% of the dataset
    df = df.dropna(subset=['Latitude','Longitude','Location'])

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce', format='%m/%d/%Y %I:%M:%S %p')

    #if the year is the same from the year from date
    mismatch = df['Year'] != df['Date'].dt.year
    if mismatch.any():
        df = df[~mismatch]

    df['Month'] = df['Date'].dt.month
    df['Day'] = df['Date'].dt.day
    df['Hour'] = df['Date'].dt.hour
    df['DayOfWeek'] = df['Date'].dt.dayofweek

    df['Working Hours'] = df['Hour'].apply(lambda x: 6 <= x < 18)
    df['Evening'] = df['Hour'].apply(lambda x: 18 <= x < 22)
    df['IsNight'] = df['Hour'].apply(lambda x: (x >= 22) or (x < 6))
    df['Weekend'] = df['DayOfWeek'].apply(lambda x: x >= 5)

    df['Month_Name'] = df['Date'].dt.strftime('%B')
    df['Day_of_Week_Name'] = df['Date'].dt.strftime('%A')

    df=df.drop_duplicates()

    #Not Year 2023
    df = df[df['Date'].dt.year!=2023]

    #Community Area - https://data.cityofchicago.org/Facilities-Geographic-Boundaries/Boundaries-Community-Areas-Map/cauq-8yn6
    community_map = {
    0: "Unknown",
    1: "Rogers Park",
    2: "West Ridge",
    3: "Uptown",
    4: "Lincoln Square",
    5: "North Center",
    6: "Lake View",
    7: "Lincoln Park",
    8: "Near North Side",
    9: "Edison Park",
    10: "Norwood Park",
    11: "Jefferson Park",
    12: "Forest Glen",
    13: "North Park",
    14: "Albany Park",
    15: "Portage Park",
    16: "Irving Park",
    17: "Dunning",
    18: "Montclare",
    19: "Belmont Cragin",
    20: "Hermosa",
    21: "Avondale",
    22: "Logan Square",
    23: "Humboldt Park",
    24: "West Town",
    25: "Austin",
    26: "West Garfield Park",
    27: "East Garfield Park",
    28: "Near West Side",
    29: "North Lawndale",
    30: "South Lawndale",
    31: "Lower West Side",
    32: "Loop",
    33: "Near South Side",
    34: "Armour Square",
    35: "Douglas",
    36: "Oakland",
    37: "Fuller Park",
    38: "Grand Boulevard",
    39: "Kenwood",
    40: "Washington Park",
    41: "Hyde Park",
    42: "Woodlawn",
    43: "South Shore",
    44: "Chatham",
    45: "Avalon Park",
    46: "South Chicago",
    47: "Burnside",
    48: "Calumet Heights",
    49: "Roseland",
    50: "Pullman",
    51: "South Deering",
    52: "East Side",
    53: "West Pullman",
    54: "Riverdale",
    55: "Hegewisch",
    56: "Garfield Ridge",
    57: "Archer Heights",
    58: "Brighton Park",
    59: "McKinley Park",
    60: "Bridgeport",
    61: "New City",
    62: "West Elsdon",
    63: "Gage Park",
    64: "Clearing",
    65: "West Lawn",
    66: "Chicago Lawn",
    67: "West Englewood",
    68: "Englewood",
    69: "Greater Grand Crossing",
    70: "Ashburn",
    71: "Auburn Gresham",
    72: "Beverly",
    73: "Washington Heights",
    74: "Mount Greenwood",
    75: "Morgan Park",
    76: "O’Hare",
    77: "Edgewater"
    }

    df['Community Name'] = df['Community Area'].map(community_map)

    ##Seasonality
    df['Season'] = df['Month'].apply(lambda x: 'Summer' if x in [3,4,5,6,7,8] else 'Winter')

    #Map Location
    def map_location(location):
        loc = str(location).upper()
    
        if re.search(r'RESIDENCE|RESIDENTIAL|HOUSE|YARD|GARAGE|PORCH|ROOMING', loc):
            return 'RESIDENCE'
    
        elif re.search(r'VEHICLE|CAR|TRUCK|TAXI|BUS|CTA|DELIVERY', loc):
            return 'VEHICLE'
    
        elif re.search(r'SCHOOL|COLLEGE|UNIVERSITY', loc):
            return 'SCHOOL/UNIVERSITY'
    
        elif re.search(r'PARK|FOREST|LAKE|RIVER|PRAIRIE|STREET', loc):
            return 'PARK/OUTDOORS'
    
        elif re.search(r'STORE|RETAIL|GROCERY|APPLIANCE|DEPARTMENT|BANK|CLEANING|PAWN|MOVIE|THEATER|RESTAURANT|BAR|TAVERN|CLUB|HOTEL|MOTEL', loc):
            return 'COMMERCIAL/RETAIL'
    
        elif re.search(r'POLICE|GOVERNMENT|JAIL|COURT|HOSPITAL|MEDICAL|CLINIC|DENTAL|FIRE|STATION|ATM', loc):
            return 'GOVERNMENT/HOSPITAL'
    
        elif re.search(r'PARKING|GARAGE', loc):
            return 'PARKING'
    
        elif re.search(r'AIRPORT|TERMINAL|VENDING|ATS|AIRCRAFT', loc):
            return 'AIRPORT'
    
        elif re.search(r'CHA', loc):
            return 'CHA BUILDING / HOUSING'
    
        elif re.search(r'VESTIBULE|LOBBY|HALLWAY|STAIRWELL|GANGWAY', loc):
            return 'BUILDING INTERIORS'
    
        elif re.search(r'BOAT|WATERCRAFT', loc):
            return 'WATER TRANSPORT'
    
        else:
            return 'OTHER'

    df['Location Group'] = df['Location Description'].apply(map_location)

    return df