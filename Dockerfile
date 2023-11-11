# Python'un resmi base imajını kullan. Burada Python'un 3.9 sürümünü kullanıyorum.
FROM python:3.9

# Çalışma dizinini /app olarak ayarla
WORKDIR /app

# Uygulamanın gereksinimlerini içeren requirements.txt dosyasını kopyala
COPY requirements.txt .

# requirements.txt dosyasında listelenen paketleri kur
RUN pip install --no-cache-dir -r requirements.txt

# Uygulamanın geri kalan dosyalarını kopyala
COPY . .

# Uygulamayı çalıştırmak için gerekli komut
CMD ["python", "./main.py"]