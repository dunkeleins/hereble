# export_ble_to_excel.py
import django
import os
import sys
import openpyxl
from django.utils import timezone

# Pfad zum Projekt hinzufügen
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Django Setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapp.settings") 
django.setup()

from bledata.models import BLEData  

# Neue Excel-Datei
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "BLE Daten"

# Header
headers = ["MAC", "RSSI", "Name", "Distanz", "Service UUID", "Herstellerdaten", "Zeitstempel"]
ws.append(headers)

# Daten einfügen

one_hour_ago = timezone.now() - timezone.timedelta(hours=1)

    # Subquery: höchsten RSSI pro MAC in letzter Stunde

#for entry in BLEData.objects.filter(timestamp__gte=one_hour_ago).order_by('-timestamp'):
for entry in BLEData.objects.all():
    ws.append([
        entry.mac,
        entry.rssi,
        entry.name,
        entry.distance,
        entry.service_uuid,
        entry.manufacturer_data,
        entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    ])

# Datei speichern
wb.save("ble_daten_export.xlsx")
print("Export abgeschlossen!")
