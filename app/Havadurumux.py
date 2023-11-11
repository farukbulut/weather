from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import requests

from app.Function import Function
from connector.MongoDBConnector import MongoDBConnector

class Havadurumux:

    def __init__(self, thread_count):
        self.connector = MongoDBConnector()
        self.thread_count = thread_count
        self.session = requests.Session()

    def add_city_thread(self, cities_list):
        for city_name, href in cities_list:
            myquery = {"link": href, "website": "havadurumux"}
            existing_documents = self.connector.find_document("links", myquery)
            last_activity_date = datetime.now() - timedelta(days=1)

            if existing_documents.count() == 0:
                mydict = {
                    "website": "havadurumux",
                    "link": href,
                    "city": city_name,
                    "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "last_activity": last_activity_date.strftime('%Y-%m-%d')
                }

                inserted_id = self.connector.add_document("links", mydict)
                print("-----------------------------------------------")
                print(f"collect_id: {inserted_id} inserted")
                print("-----------------------------------------------")

    def fetch_cities(self):
        response = self.session.get("https://www.havadurumux.net/tum-sehirler/")
        cities_list = []
        if response.content:
            soup = BeautifulSoup(response.content, 'html.parser')
            div = soup.find("div", {"class": "tumiller"})
            ul_elements = div.find_all("li") if div else []
            for city in ul_elements:
                town = city.find("a")
                href = town.get("href") if town else ''
                city_name = town.text if town else ''
                cities_list.append((city_name, href))
        return cities_list

    def add_city(self):
        cities_list = self.fetch_cities()
        with ThreadPoolExecutor(max_workers=self.thread_count) as executor:
            for i in range(self.thread_count):
                thread_cities = cities_list[i::self.thread_count]
                executor.submit(self.add_city_thread, thread_cities)

    def fetch_weather_data(self, link_docs):
        for link_doc in link_docs:
            functions = Function()
            url = link_doc["link"]
            provincial_plate = link_doc["plate_no"]

            response = self.session.get(url)
            if response.content:
                soup = BeautifulSoup(response.content, 'html.parser')
                weather = soup.find("table", {"id": "hor-minimalist-a"})
                weather_li = weather.find("tbody").find_all("tr")[1:8]

                for city in weather_li:
                    date_text = city.find("td").text
                    date_text = functions.convert_turkish_month_to_english(date_text.split(',')[0])
                    temp_high = city.find_all("td")[2].text.replace('°', '').strip()
                    temp_low = city.find_all("td")[3].text.replace('°', '').strip()

                    try:
                        parsed_date = datetime.strptime(date_text, "%d %B %Y")
                        temp_high_val = float(temp_high)
                        temp_low_val = float(temp_low)

                        existing_data = self.connector.find_document("weather_data",
                                                                     {"provincial_plate": provincial_plate,
                                                                      "date": parsed_date})
                        if existing_data.count() > 0:
                            self.connector.update_document(
                                "weather_data",
                                {"provincial_plate": provincial_plate, "date": parsed_date},
                                {"$set": {
                                    "weather.havadurumux.temp_high": temp_high_val,
                                    "weather.havadurumux.temp_low": temp_low_val
                                }}
                            )
                            print(f"Data updated for plate: {provincial_plate}, date: {parsed_date}")
                        else:
                            self.connector.add_document("weather_data", {
                                "provincial_plate": provincial_plate,
                                "date": parsed_date,
                                "weather": {
                                    "havadurumux": {
                                        "temp_high": temp_high_val,
                                        "temp_low": temp_low_val
                                    }
                                }
                            })
                            print(f"Data insert for plate: {provincial_plate}, date: {parsed_date}")
                    except ValueError as e:
                        print(f"Error parsing date or temperature: {e}")

                self.connector.update_document(
                    "links",
                    {"link": url},
                    {"$set": {
                        "last_activity": datetime.now().strftime('%Y-%m-%d')
                    }}
                )

    def add_weather(self):
        function = Function()
        links = function.get_links("havadurumux")
        with ThreadPoolExecutor(max_workers=self.thread_count) as executor:
            for i in range(self.thread_count):
                thread_links = links[i::self.thread_count]
                executor.submit(self.fetch_weather_data, thread_links)