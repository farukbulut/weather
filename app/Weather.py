import threading
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import requests
from app.Function import Function
from connector.MongoDBConnector import MongoDBConnector
import queue

class Weather:

    def __init__(self, thread_count):
        self.connector = MongoDBConnector()
        self.thread_count = thread_count
        self.session = requests.Session()

    def get_weather_data(self, city_name):
        url = "https://weather.com/api/v1/p/redux-dal"
        payload = [
            {
                "name": "getSunV3LocationSearchUrlConfig",
                "params": {
                    "query": city_name + " Türkiye",
                    "language": "tr-TR",
                    "locationType": "locale"
                }
            }
        ]
        response = self.session.post(url, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Hata: {response.status_code}")
            return None

    def process_and_store_response(self, city_name):
        response = self.get_weather_data(city_name)
        if response:
            # API yanıtını işleme ve MongoDB'ye kaydetme
            for key, value in response['dal']['getSunV3LocationSearchUrlConfig'].items():
                if 'data' in value:
                    address_list = value['data']['location']['address']
                    for i, location_data in enumerate(address_list):
                        if 'Türkiye' in location_data:
                            # İlgili verileri ayıklama

                            place_id = value['data']['location']['placeId'][i]
                            postal_code = value['data']['location']['postalCode'][i]
                            plate_no = postal_code[:2]  # Posta kodunun ilk iki karakterini al

                            # Oluşturulan URL
                            link = f"https://weather.com/tr-TR/weather/tenday/l/{place_id}"

                            myquery = {"plate_no": plate_no, "website": "weather"}

                            document_count = self.connector.get_collection("links").count_documents(myquery)
                            if document_count == 0:
                                # MongoDB'de 'weather_urls' koleksiyonuna kaydetme

                                last_activity_date = datetime.now() - timedelta(days=1)
                                document = {
                                    'city': city_name,
                                    'plate_no': plate_no,
                                    'link': link,
                                    'website': 'weather',
                                    "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    "last_activity": last_activity_date.strftime('%Y-%m-%d')
                                }
                                self.connector.add_document('links', document)

                                # 'links' koleksiyonundaki ilgili şehrin linkini güncelle
                                update_query = {'city': city_name, 'website': 'havadurumux'}
                                new_values = {"$set": {'plate_no': plate_no}}
                                self.connector.update_document('links', update_query, new_values)
                                print(f"{city_name} için veri kaydedildi ve güncellendi: {link}")

                            # İlk eşleşme kaydedildikten sonra döngüden çık
                            break

    def worker(self, city_queue):
        while not city_queue.empty():
            city_name = city_queue.get()
            self.process_and_store_response(city_name)
            city_queue.task_done()

    def add_city(self):
        city_documents = self.connector.find_document('links', {'website': 'havadurumux'})
        city_queue = queue.Queue()
        for city_document in city_documents:
            city_queue.put(city_document['city'])

        with ThreadPoolExecutor(max_workers=self.thread_count) as executor:
            for _ in range(self.thread_count):
                executor.submit(self.worker, city_queue)

    def fetch_weather_data(self, link_docs):
        for link_doc in link_docs:
            functions = Function()
            url = link_doc["link"]
            provincial_plate = link_doc["plate_no"]

            response = self.session.get(url)
            if response.content:
                soup = BeautifulSoup(response.content, 'html.parser')
                weather = soup.find("div", {"class": "Card--content--1GQMr DailyForecast--CardContent--2YlvT"})
                weather_li = weather.find_all("details")[1:8]

                for city in weather_li:
                    temp_high = city.find("span", {"data-testid": "TemperatureValue"}).text
                    temp_low = city.find("span", {"data-testid": "lowTempValue"}).text
                    date_text = city.find("h3", {"data-testid": "daypartName"}).text

                    try:
                        current_year = datetime.now().year
                        current_month = datetime.now().month
                        day_name_tr = date_text.split()[0]
                        day_name_en = functions.translate_day_name(day_name_tr)
                        parsed_date = datetime.strptime(
                            f"{current_year}-{current_month}-{date_text.split()[1]} {day_name_en}",
                            "%Y-%m-%d %a")

                        temp_high_val = functions.extract_number(temp_high)
                        temp_low_val = functions.extract_number(temp_low)


                        document_count = self.connector.get_collection("weather_data").count_documents(
                            {
                                "provincial_plate": provincial_plate,
                                "date": parsed_date
                             }
                        )

                        if document_count > 0:
                            self.connector.update_document(
                                "weather_data",
                                {"provincial_plate": provincial_plate, "date": parsed_date},
                                {"$set": {
                                    "weather.weather.temp_high": temp_high_val,
                                    "weather.weather.temp_low": temp_low_val
                                }}
                            )
                            print(f"Data updated for plate: {provincial_plate}, date: {parsed_date}")
                        else:
                            self.connector.add_document("weather_data", {
                                "provincial_plate": provincial_plate,
                                "date": parsed_date,
                                "weather": {
                                    "weather": {
                                        "temp_high": temp_high_val,
                                        "temp_low": temp_low_val
                                    }
                                }
                            })
                            print(f"Data inserted for plate: {provincial_plate}, date: {parsed_date}")
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
        links = function.get_links("weather")
        threads = []

        for i in range(self.thread_count):
            thread_links = links[i::self.thread_count]
            thread = threading.Thread(target=self.fetch_weather_data, args=(thread_links,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()
