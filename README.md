# Hava Durumu Verileri

Projeyi farklı ortamlarda çalıştırmak için gerekli kurulum adımları aşağıda belirtilmiştir. Docker kullanmayacaksanız, config.py dosyasında MongoDB adresini uygun şekilde güncellemeyi unutmayın.
# Conda Kullanıcıları İçin Kurulum
Anaconda ortamında gerekli paketleri kurmak için aşağıdaki komutları kullanın:
```sh
conda install -c anaconda beautifulsoup4
conda install -c anaconda pymongo
conda install -c anaconda requests
```

# Python pip Kütüphanesi Kullanıcıları İçin Kurulum
pip ile gerekli paketleri kurmak için aşağıdaki komutları kullanın:
```sh
conda pip install -a beautifulsoup4
conda pip install -a pymongo
conda pip install -a requests
```

# Docker Kullanıcıları İçin Kurulum
Docker kullanıyorsanız, projeyi başlatmak için aşağıdaki komutu kullanın:
```sh
docker compose up 
```