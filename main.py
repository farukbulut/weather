import datetime
from app.Havadurumux import Havadurumux
from app.Metoffice import Metoffice
from app.Weather import Weather

def run_weather():
    thread_count = 20 # Çalıştırmak istediğiniz thread sayısı

    start_time = datetime.datetime.now()
    print(f"İşlem başlangıç zamanı: {start_time}")

    havadurumux = Havadurumux(thread_count)
    weather = Weather(thread_count)
    metoffice = Metoffice(thread_count)

    havadurumux.add_city()
    weather.add_city()
    metoffice.add_city()

    havadurumux.add_weather()
    weather.add_weather()
    metoffice.add_weather()

    end_time = datetime.datetime.now()
    print(f"İşlem bitiş zamanı: {end_time}")

    duration = end_time - start_time
    print(f"Toplam süre: {duration}")

# Fonksiyonu çağırarak işlemleri başlatın
run_weather()