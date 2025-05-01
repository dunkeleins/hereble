# This script updates the names of BLE devices in the database based on their MAC addresses.
import django
import os
import sys
from django.utils.timezone import make_aware
from datetime import datetime



# Pfad zum Projekt hinzufügen
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Django Setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapp.settings") 
django.setup()

from bledata.models import BLEData  
mac_name_map = {
    "56:97:f0:56:3c:73": "Apple Watch",
    "74:d7:7a:7a:50:2a": "Apple Watch",
    "c4:86:62:cd:28:57": "Apple Watch",
    "fa:fe:14:79:c2:be": "Apple Watch",
    "6e:65:0e:52:f7:9c": "Apple Watch",
    "73:1c:bc:1e:91:c7": "Apple Watch",
    "ec:e8:04:a0:b4:9f": "Apple Watch",
    "f8:5d:61:b6:23:db": "Apple Watch",
    "53:6c:35:32:3e:4d": "Apple Watch",
    "51:55:e4:49:c9:2c": "Apple Watch",
    "e2:ad:01:8b:08:ea": "Apple Watch",
    "d5:0c:cf:8a:50:7a": "Apple Watch",
    "5d:fc:48:db:78:3e": "Apple Watch",
    "c7:8b:9e:f9:56:2f": "Apple Watch",
    "c7:69:8c:d2:d7:91": "Apple Watch",
    "75:fe:9a:af:f1:b3": "Apple Watch",
    "f2:95:65:99:79:0e": "Apple Watch",
    "75:e6:26:7c:7a:20": "Apple Watch",
    "db:6a:5a:9d:69:1f": "Apple Watch",
    "40:68:bb:7b:55:c5": "Apple Watch",
    "d3:e9:0b:2a:77:1d": "Apple Watch",
    "62:c5:96:52:4f:80": "Apple Watch",
    "56:bf:29:5a:03:f5": "Apple Watch",
    "d4:aa:e5:c1:c8:10": "Apple Watch",
    "7a:f5:9d:8f:95:0f": "Apple Watch",
    "d7:4c:14:31:7b:b7": "Apple Watch",
    "e2:96:ff:96:5a:ec": "Apple Watch",
    "5a:f1:6c:5a:c5:60": "Apple Watch",
    "f2:a0:6d:93:09:6c": "Apple Watch",
    "51:ac:88:22:34:8c": "Apple Watch",
    "44:bb:8e:bf:1b:df": "Apple Watch",
    "12:34:56:78:9A:BC": "Apple iPhone",
    "4f:3b:6b:fe:e9:6a": "Apple iPhone",
    "67:b6:bf:9b:c7:01": "Apple iPhone",
    "ee:2e:a4:30:d7:35": "Apple iPhone",
    "51:1b:cd:aa:60:da": "Apple iPhone",
    "f3:13:b3:33:a0:eb": "Apple iPhone",
    "65:40:0d:af:1f:01": "Apple iPhone",
    "5f:b1:1f:37:b7:b8": "Apple iPhone",
    "f3:13:b3:33:a0:eb": "Apple iPhone",
    "6f:a6:74:52:de:83": "Apple iPhone",
    "46:50:ba:92:9f:81": "Apple iPhone",
    "6f:1d:c2:fd:7a:7d": "Apple iPhone",
    "72:e5:cb:91:a2:5e": "Apple iPhone",
    "69:94:52:00:67:c4": "Apple iPhone",
    "ff:5b:bb:b8:44:a2": "Apple iPhone",
    "65:c4:01:98:90:47": "Apple iPhone",
    "65:d1:5c:89:96:a5": "Apple iPhone",
    "c1:e7:30:43:9d:31": "Apple iPhone",
    "e4:81:82:a7:d2:8d": "Apple iPhone",
    "73:be:fa:47:f2:12": "Apple iPhone",
    "63:05:f3:b4:0f:99": "Apple iPhone",
    "65:c4:01:98:90:47": "Apple iPhone",
    "65:d1:5c:89:96:a5": "Apple iPhone",
    "c1:e7:30:43:9d:31": "Apple iPhone",
    "59:f6:7f:2d:74:f2": "Apple iPhone",
    "f5:69:a8:08:7a:72": "Apple iPhone",
    "7e:ef:5b:3d:27:ae": "Apple iPhone",
    "7e:ef:5b:3d:27:ae": "Apple iPhone",
    "40:14:c3:5b:3e:a8": "Apple iPhone",
    "7e:ef:5b:3d:27:ae": "Apple iPhone",
    "cd:b3:91:8e:d4:04": "Apple iPhone",
    "40:14:c3:5b:3e:a8": "Apple iPhone",
    "7e:ef:5b:3d:27:ae": "Apple iPhone",
    "cd:b3:91:8e:d4:04": "Apple iPhone",
    "d7:ac:7a:29:90:88": "Apple iPhone",
    "53:1a:cb:94:1f:2c": "Apple iPhone",
    "53:80:07:12:bf:97": "Apple iPhone",
    "ef:03:77:b5:77:aa": "Apple iPhone",
    "da:b0:74:12:56:3f": "Apple iPhone",
    "5e:6c:f1:ce:70:8b": "Apple iPhone",
    "56:e9:1e:17:6e:95": "Apple iPhone",
    "f2:3e:e4:8c:15:07": "Apple iPhone",
    "f6:13:81:20:e4:e7": "Apple iPhone",
    "71:9e:5f:be:1a:2b": "Apple iPhone",
    "5d:5e:04:ab:b5:26": "Apple iPhone",
    "59:35:49:6f:d3:28": "Apple iPhone",
    "47:5c:13:9c:d3:f4": "Apple iPhone",
    "f6:13:81:20:e4:e7": "Apple iPhone",
    "5c:ee:32:b1:21:20": "Apple iPhone",
    "5d:fc:b4:43:f4:9e": "Apple iPhone",
    "f9:d8:7e:97:08:d1": "Apple iPhone",
    "65:c0:67:5e:07:90": "Apple iPhone",
    "65:c0:67:5e:07:90": "Apple iPhone",
    "7a:70:03:ce:23:20": "Apple iPhone",
    "42:c6:ee:ba:21:21": "Apple iPhone",
    "50:f8:b0:05:a2:e5": "Apple iPhone",
    "ec:e4:16:5c:2a:69": "Apple iPhone",
    "cf:43:d2:18:20:9d": "Apple iPhone",
    "d8:ef:b2:49:17:7b": "Apple Airpods",
    "4d:eb:02:87:c4:c8": "Apple Airpods",
    "4d:e2:bb:19:e8:df": "Apple Airpods",
    "da:58:55:1a:4c:68": "Apple Airpods",
    "fa:86:99:24:57:83": "Apple Airpods",
    "cc:e9:ed:f8:ba:a8": "Apple Airpods",
    "4b:e1:39:53:c3:fa": "Apple Airpods",
    "67:c5:89:da:a1:fb": "Apple Airpods",
    "e0:63:eb:74:91:35": "Apple Airpods",
    "67:9b:7b:9d:cb:e1": "Apple Airpods",
    "55:d0:ce:21:65:4f": "Apple Airpods",
    "f2:35:6e:fc:3a:05": "Apple Airpods",
    "c4:bd:73:48:c4:a6": "Apple Airpods",
    "cd:49:39:90:69:a2": "Apple Airpods",
    "cd:49:39:90:69:a2": "Apple Airpods",
    "c1:23:62:12:82:d3": "Apple Airpods",
    "56:97:ae:4f:00:c0": "Apple Airpods",
    "ec:c2:ca:87:50:4b": "Apple Airpods",
    "e6:7b:06:ed:65:b3": "Apple Airpods",
}

for mac, name in mac_name_map.items():
    BLEData.objects.filter(mac=mac).update(name=name)

start = make_aware(datetime(2025, 4, 4, 0, 0, 0))
end = make_aware(datetime(2025, 4, 12, 23, 59, 59))
BLEData.objects.filter(timestamp__range=(start, end)).update(environment="Crowded")

start = make_aware(datetime(2025, 4, 13,  0, 0, 0))
end = make_aware(datetime(2025, 4, 20, 23, 59, 59))
BLEData.objects.filter(timestamp__range=(start, end)).update(environment="Open")

start = make_aware(datetime(2025, 4, 21, 0, 0, 0))
end = make_aware(datetime(2025, 4, 21, 23, 59, 59))
BLEData.objects.filter(timestamp__range=(start, end)).update(environment="Open2")

start = make_aware(datetime(2025, 4, 18, 0, 0, 0))
end = make_aware(datetime(2025, 4, 18, 23, 59, 59))
BLEData.objects.filter(timestamp__range=(start, end)).update(environment="Crowded")

start = make_aware(datetime(2025, 4, 22, 0, 0, 0))
end = make_aware(datetime(2025, 4, 26, 23, 59, 59))
BLEData.objects.filter(timestamp__range=(start, end)).update(environment="Crowded")

print("Datenbank aktualisiert!")