from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import requests
from app.Function import Function
from connector.MongoDBConnector import MongoDBConnector

class Metoffice:

    def __init__(self, thread_count):
        self.connector = MongoDBConnector()
        self.thread_count = thread_count
        self.session = requests.Session()

    def add_city_thread(self, city_tuple):
        city_name, href = city_tuple
        func = Function()
        city_name = func.correct_city_name(city_name)

        myquery = {"link": href, "website": "metoffice"}
        document_count = self.connector.get_collection("links").count_documents(myquery)
        if document_count == 0:
            query_for_plate = {"city": city_name, "website": "havadurumux"}
            plate_count = self.connector.get_collection("links").count_documents(query_for_plate)
            last_activity_date = datetime.now() - timedelta(days=1)

            mydict = {
                "website": "metoffice",
                "link": href,
                "city": city_name,
                "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "last_activity": last_activity_date.strftime('%Y-%m-%d')
            }

            if plate_count > 0:
                existing_plate_document = self.connector.find_document("links", query_for_plate)
                plate_no = existing_plate_document[0].get('plate_no')
                if plate_no:
                    mydict['plate_no'] = plate_no

            inserted_id = self.connector.add_document("links", mydict)
            print(f"collect_id: {inserted_id} inserted for {city_name}")

    def fetch_cities(self):
        r = self.session.get("https://www.metoffice.gov.uk/weather/world/turkey/list")
        cities_list = []
        if r.content:
            soup = BeautifulSoup(r.content, 'html.parser')
            section = soup.find("section", {"class": "link-group-container link-group-padded double-column"})
            cities = section.find_all("ul", {"class": "link-group-list"})

            for city_ul in cities:
                li_elements = city_ul.find_all("li")
                for li in li_elements:
                    city_name = li.find("span").text.strip()
                    href = "https://www.metoffice.gov.uk" + li.find("a")["href"].strip()
                    cities_list.append((city_name, href))
        return cities_list

    def add_city(self):
        cities_list = self.fetch_cities()
        with ThreadPoolExecutor(max_workers=self.thread_count) as executor:
            for city_tuple in cities_list:
                executor.submit(self.add_city_thread, city_tuple)

    def fetch_weather_data(self, link_doc):
        url = link_doc["link"]
        provincial_plate = link_doc["plate_no"]

        r = self.session.get(url)
        if r.content:
            soup = BeautifulSoup(r.content, 'html.parser')
            weather = soup.find("ul", {"id": "dayNav"})
            if weather:
                weather_li = weather.find_all("li")[1:8]

                for city in weather_li:
                    date = city.find("time")
                    temp_high = city.find("span", {"class": "tab-temp-high"})
                    temp_low = city.find("span", {"class": "tab-temp-low"})

                    if date and temp_high and temp_low:
                        date_string = date.get("datetime").split("T")[0]

                        try:
                            parsed_time = datetime.strptime(date_string, "%Y-%m-%d")
                            temp_high_val = float(temp_high.get("data-value").strip())
                            temp_low_val = float(temp_low.get("data-value").strip())

                            document_count = self.connector.get_collection("weather_data").count_documents(
                                {
                                    "provincial_plate": provincial_plate,
                                    "date": parsed_time
                                }
                            )

                            if document_count > 0:
                                self.connector.update_document(
                                    "weather_data",
                                    {"provincial_plate": provincial_plate, "date": parsed_time},
                                    {"$set": {
                                        "weather.metoffice.temp_high": temp_high_val,
                                        "weather.metoffice.temp_low": temp_low_val
                                    }}
                                )
                                print(f"Data updated for plate: {provincial_plate}, date: {parsed_time}")
                            else:
                                self.connector.add_document("weather_data", {
                                    "provincial_plate": provincial_plate,
                                    "date": parsed_time,
                                    "weather": {
                                        "metoffice": {
                                            "temp_high": temp_high_val,
                                            "temp_low": temp_low_val
                                        }
                                    }
                                })
                                print(f"New data inserted for plate: {provincial_plate}, date: {parsed_time}")

                            self.connector.update_document(
                                "links",
                                {"link": url},
                                {"$set": {
                                    "last_activity": datetime.now().strftime('%Y-%m-%d')
                                }}
                            )

                        except ValueError as e:
                            print(f"Error parsing date: {e}")

    def add_weather(self):
        function = Function()
        links = function.get_links("metoffice")
        with ThreadPoolExecutor(max_workers=self.thread_count) as executor:
            for link_doc in links:
                executor.submit(self.fetch_weather_data, link_doc)