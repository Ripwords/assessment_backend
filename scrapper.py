from SubwayScrapper import *
import json

# Create an instance of the SubwayScrapper class
scrapper = SubwayScrapper("https://subway.com.my/find-a-subway", location="kuala lumpur")

# Selectors
search_bar = "input#fp_searchAddress"
location_list = "div.fp_ll_holder"
result_items = "div.fp_listitem"

# Location Name Selector
name_selector = "div.location_left > h4"

# Location Info (Address & Operating hours) Selector
info_selector = "div.location_left > div.infoboxcontent > p"

# Location Direction Selector
direction_selector = "div.location_right > div.directionButton > a"

database = scrapper.generate_database(search_bar, location_list, result_items, name_selector, info_selector, direction_selector)

# print(scrapper.geocode("Wangsa Ave, Bandar Wangsa Maju, #9 Jalan Perdana 1, G-52, Wangsa Walk Mall, Kuala Lumpur, 53300"))

# Output database to json file
with open('data.json', 'w') as json_file:
    json.dump(database, json_file)