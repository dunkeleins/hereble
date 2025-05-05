# This script updates the names of BLE devices in the database based on their MAC addresses.
import django
import os
import sys
import hashlib
from django.utils.timezone import make_aware
from datetime import datetime

SALT = os.environ["BLE_SALT"].encode()

# Pfad zum Projekt hinzufügen
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Django Setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapp.settings") 
django.setup()

from bledata.models import BLEData  
# update mac_hash in the database
def update_mac_hash():
    # Alle BLEData-Objekte abrufen
    ble_data_objects = BLEData.objects.all()

    for obj in ble_data_objects:
        # MAC-Adresse und SALT kombinieren 
        mac_with_salt = (obj.mac + SALT.decode()).encode()
        # SHA-256 Hash der kombinierten Zeichenfolge erstellen 
        mac_hash = hashlib.sha256(mac_with_salt).hexdigest()
        # Hash in das Objekt speichern
        obj.mac_hash = mac_hash

    # Alle Änderungen speichern
    BLEData.objects.bulk_update(ble_data_objects, ['mac_hash'])
    # Optional: Ausgabe der aktualisierten Objekte
    return ble_data_objects

update_mac_hash()

print("Datenbank aktualisiert!")