# hereble
Bluetooth Low Energy ESP32 Beacon sammelt Daten von BLE Geräten in der Umgebung und sendet diese an einen zentralen Webservice auf Basis des Python Frameworks Django. Ein gemeinsames Netzwerk vorausgesetzt.
![systemarchitektur](https://github.com/user-attachments/assets/b7d30024-ccfb-4a7b-a473-67f740872058)

## analyse:
- Machine Learning Test zum unterscheiden von statischen oder bewegten Geräten.

## simplearduino:
- sketch_herble:
    ESP32 Programm zum scannen nach BLE Geräten. Liefert den Output über die serielle Schnittstelle.
- sketch_herble_simple_nb:
    ESP32 Programm zum scannen nach BLE Geräten. Sendet die Daten im JSON Format an einen Webservice.
- sketch_hereble_webservice:
    ESP32 Programm zum scannen nach BLE Geräten. Bietet einen eigenen Webservice am Gerät, der die gemessenen Daten über einen Broeser anzeigt.

## webapp:
- webapp:
    WebApp Python Framwork Django empfängt JSON Daten und speichert diese in der SQLLite Datenbank. Zusätzliches Webfrontend ermöglicht die Anzeige der Daten in grafischer und tabellarischer Form.

Starten der WebApp auf Port 80 (unsicher): 
```
    py manage.py runserver 192.168.137.1:80 
```

Starten der WebApp auf Port 443 mit SSL Verschlüsselung, Zertifikate müssen angelegt oder eingebunden werden, sind nicht teil des Repositories: 
```
    py manage.py runserver_plus 192.168.137.1:443 --cert-file ../hereblewebapp/sslcert/localhost.crt --key-file ../herblewebapp/sslcert/localhost.key
```

# Notwendige Dateien und Konfigurationen
## constants_ble.h:
Diese Datei wird benötigt um den Arduino Sketch auf dem ESP32 zu kompilieren.
```
const char* ssid = "xxxx";
const char* password = "xxxx";
const char* serverUrl = "https://ip.ip.ip.ip/sendbledata/";
const char* salt = "salt"; 
const char* root_ca = \
"-----BEGIN CERTIFICATE-----\n" \
"MIID...Certificate... \n" \
"-----END CERTIFICATE-----\n";
*/
```

## Self signed Zertifikat Erstellung nur für den lokalen Gebrauch geeignet
```
mkdir sslcert && cd sslcert
```
### generate private key
```
openssl genrsa -out localhost.key 2048
```
### generate self signed vertificate valid 365 days
```
openssl req -new -x509 -key localhost.key -out localhost.crt -days 365 \
  -subj "/C=AT/ST=Tirol/L=Innsbruck/O=BachelorarbeitIndra/CN=localhost"
```
### insert ca to constants_ble.h on ESP32
```
cat sslcert/localhost.crt
```
```
const char* root_ca = \
"-----BEGIN CERTIFICATE-----\n" \
"MIID...dein Zertifikat...\n" \
"...\n" \
"-----END CERTIFICATE-----\n";
```
