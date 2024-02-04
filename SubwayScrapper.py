import requests

from os import environ
from time import sleep
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.options import Options

# Headless Chrome Options
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")

# Load the API Key from the .env file
load_dotenv()
API_KEY = environ.get("GEOCODE_API_KEY")

# SubwayScrapper Class
class SubwayScrapper:
    def __init__(self, url, location="")->None:
        self.url = url
        self.location = location

        self.api_key = API_KEY
        self.driver = webdriver.Chrome(options=chrome_options)

    def load_page(self)->None:
        self.driver.get(self.url)
        self.driver.implicitly_wait(10)

    def geocode(self, address: str)->dict:
        # Attempt to geocode the address
        # If address is not found, remove the first element (Unit No., Floor, etc.) and try again
        for _ in range(2):
            url = f"https://maps.googleapis.com/maps/api/geocode/json?"
            response = requests.get(url, params={
                "address": address,
                "key": self.api_key
            })
            data = response.json()
            if (data["status"] == "ZERO_RESULTS"):
                # Remove the first element (Unit No., Floor, etc.) and try again
                address = ",".join(address.split(",")[1:])
                continue
            elif (len(data["results"]) > 0):
                # If the address is found, return the coordinates
                break
            else:
                # Something went wrong, return None
                return None
        try:
            # Attempt to return the coordinates
            return data["results"][0]["geometry"]["location"]
        except IndexError:
            # If the address is not found, return None
            # print(data) # Debugging
            return None

    def get_locations(self, search_bar: str, location_list: str, result_items: str)->list:
        """
        The function `get_locations` finds a location input element, enters a location, presses enter,
        waits for the results, collects the results, and returns them as a list.
        
        Parameters:
            search_bar (str): The CSS selector for the location input element
            location_list (str): The CSS selector for the location list
            result_items (str): The CSS selector for the result items

        Returns:
            list: A list of result items (locations)
        """
        # Find the location input element, enter location, and press enter
        location_input: WebElement = self.driver.find_element(By.CSS_SELECTOR, search_bar)
        location_input.send_keys(self.location)
        location_input.send_keys(u'\ue007') # Press Enter

        # Wait for the results to be filtered
        sleep(3)

        # Collect the results
        location_list: WebElement = self.driver.find_element(By.CSS_SELECTOR, location_list)
        # Exclude the locations that are not displayed
        locations: list[WebElement] = location_list.find_elements(By.CSS_SELECTOR, result_items+":not([style*=none])")
        return locations
    
    def extract_info(self, location: WebElement, name_selector: str, info_selector: str, direction_selector: str)->dict:
        """
        The function `extract_info` extracts the name, info, and direction of a location.

        Parameters:
            location (WebElement): The location element
            name_selector (str): The CSS selector for the name of the location
            info_selector (str): The CSS selector for the info of the location
            direction_selector (str): The CSS selector for the direction of the location

        Returns:
            dict: A dictionary containing the name, info, and direction of the location
            The schema is as follows:\n
            [
              {
                "name": "Subway Name",
                "info": {
                  "address": "Subway Address",
                  "operating_hours": ["Subway Operating Hours 1", "Subway Operating Hours 2", ...]
                },
                "direction": {
                  "gmap": "Google Maps Link",
                  "waze": "Waze Link"
                }
              }
            ]
        """
        # Extract the name
        name: WebElement = location.find_element(By.CSS_SELECTOR, name_selector).text

        # Extract the info
        info: list[WebElement] = location.find_elements(By.CSS_SELECTOR, info_selector)
        info = [p.text if len(p.text) > 0 else None for p in info]
        info = list(filter(None, info))
        
        # If len(info) is 0, then the location is filtered out (outside location search)
        if len(info) == 0:
            return None
        
        # Extract the direction
        direction: list[WebElement] = location.find_elements(By.CSS_SELECTOR, direction_selector)
        gmap_link = direction[0].get_attribute("href")
        waze_link = direction[1].get_attribute("href")

        return {
            "name": name,
            "info": {
                "address": info[0],
                "coordinates": self.geocode(info[0]),
                "operating_hours": info[1:]
            },
            "direction": {
                "gmap": gmap_link,
                "waze": waze_link
            }
        }
    
    def generate_database(self, search_bar: str, location_list: str, result_items: str, name_selector: str, info_selector: str, direction_selector: str):
        """
        The function `generate_database` scrapes the page, collects the locations, and extracts the name, info, and direction of each location.

        Parameters:
            search_bar (str): The CSS selector for the location input element
            location_list (str): The CSS selector for the location list
            result_items (str): The CSS selector for the result items
            name_selector (str): The CSS selector for the name of the location
            info_selector (str): The CSS selector for the info of the location
            direction_selector (str): The CSS selector for the direction of the location

        Returns:
            dict: A dictionary containing the name, info, and direction of the location
            The schema is as follows:\n
            [
              {
                "name": "Subway Name",
                "info": {
                  "address": "Subway Address",
                  "operating_hours": ["Subway Operating Hours 1", "Subway Operating Hours 2", ...]
                },
                "direction": {
                  "gmap": "Google Maps Link",
                  "waze": "Waze Link"
                }
              }
            ]
        """
        # Scrap the page
        self.load_page()
        locations = self.get_locations(search_bar, location_list, result_items)
        
        # Database is a list of dictionaries
        # Each dictionary contains the name, info, and direction of a location
        database = [self.extract_info(location, name_selector, info_selector, direction_selector) for location in locations]
        database = list(filter(None, database))

        self.driver.quit()

        return database