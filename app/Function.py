import re
from datetime import datetime

from connector.MongoDBConnector import MongoDBConnector


class Function:

    @classmethod
    def extract_number(self,text):
        match = re.search(r'\d+', text)
        return float(match.group()) if match else None

    @classmethod
    def convert_turkish_month_to_english(self, date_text):
        months = {
            "Ocak": "January", "Şubat": "February", "Mart": "March",
            "Nisan": "April", "Mayıs": "May", "Haziran": "June",
            "Temmuz": "July", "Ağustos": "August", "Eylül": "September",
            "Ekim": "October", "Kasım": "November", "Aralık": "December"
        }
        for tr, en in months.items():
            date_text = date_text.replace(tr, en)
        return date_text

    # Türkçe gün adlarını İngilizce karşılıklarına çeviren fonksiyon
    def translate_day_name(self, day_name_tr):
        tr_to_en = {
            "Pzt": "Mon",
            "Sal": "Tue",
            "Çar": "Wed",
            "Per": "Thu",
            "Cum": "Fri",
            "Cmt": "Sat",
            "Paz": "Sun"
        }
        return tr_to_en.get(day_name_tr[:3], day_name_tr)

    def get_links(self, website):
        connector = MongoDBConnector()
        today = datetime.now().strftime('%Y-%m-%d')
        query = {"website": website, "last_activity": {"$lt": today}, "plate_no": {"$exists": True}}
        links_cursor = connector.find_document("links", query)
        links = list(links_cursor)
        return links

    def correct_city_name(self, city_name):
        city_corrections = {
            "Canakkale": "Çanakkale",
            "Corum": "Çorum",
            "Diyarbakir": "Diyarbakır",
            "Gumushane": "Gümüşhane",
            "Istanbul": "İstanbul",
            "Izmir": "İzmir",
            "Kirsehir": "Kırşehir",
            "Kutahya": "Kütahya",
            "Mugla": "Muğla",
            "Nigde": "Niğde",
            "Sirnak": "Şırnak",
            "Tekirdag": "Tekirdağ",
            "Usak": "Uşak"
        }

        # city_name değişkenini kontrol et ve gerekirse düzelt
        return city_corrections.get(city_name, city_name)