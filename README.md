# hereble
Bluetooth Low Energy ESP32 Beacon collects data and sends to central service.

## analyse:
- Machine Learning test for moving or static devices

## simplearduino:
- sketch_herble:
    ESP32 program to scan for BLE devices and send information on serial output.
- sketch_herble_simple_nb:
    ESP32 program to send BLE informations in JSON format to a http service.
- sketch_hereble_webservice:
    ESP32 program runs a webservice on ESP32

## webapp:
- webapp:
    WebApp in Python Django recieves JSON format and logs to database.

To run the webapp for view only on http: 
```
    py manage.py runserver 192.168.137.1:80 
```

To run the webapp for datagathering on https: 
```
    py manage.py runserver_plus 192.168.137.1:443 --cert-file ../hereblewebapp/sslcert/localhost.crt --key-file ../herblewebapp/sslcert/localhost.key
```


# Self signed certificate generation
```
mkdir sslcert && cd sslcert
```
## generate private key
```
openssl genrsa -out localhost.key 2048
```
## generate self signed vertificate valid 365 days
```
openssl req -new -x509 -key localhost.key -out localhost.crt -days 365 \
  -subj "/C=DE/ST=NRW/L=City/O=Firma/CN=localhost"
```
## insert ca to constants_ble.h on ESP32
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