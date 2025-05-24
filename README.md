# hereble
Bluetooth Low Energy ESP32 Beacon collects data and sends to central service.

## analyse:
- Machine Learning test for moving or static devices

## simplearduino:
- sketch_herble:
    ESP32 program to scan for BLE devices and send information on serial output.
- sketch_herble_simple_nb:
    ESP32 program to send BLE informations in JSON format to a http service. Final version.
- sketch_hereble_webservice:
    ESP32 program runs a webservice on ESP32 and can be accessed from browser after connected to accesspoint HereBLE

## webapp:
- webapp:
    WebApp in Python Django recieves JSON format and logs to database.

To run the webapp for view only on http: 
```
    py manage.py runserver 192.168.137.1:80 
```

To run the webapp for datagathering on https (certificates not in source): 
```
    py manage.py runserver_plus 192.168.137.1:443 --cert-file ../hereblewebapp/sslcert/localhost.crt --key-file ../herblewebapp/sslcert/localhost.key
```

# Necessary files and configurations
## constants_ble.h:
This file is needed to run the arduino sketch on ESP32
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

## Self signed certificate generation for local usage only
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