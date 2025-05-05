# hereble
Bluetooth Low Energy ESP32 Beacon collects data and sends to central service.

## simplearduino:
- sketch_herble:
    ESP32 program to scan for BLE devices and send information on serial output.
- sketch_herble_simple_nb:
    ESP32 program to send BLE informations in JSON format to a http service.
- sketch_hereble_webservice:
    ESP32 program runs a webservice on ESP32

## webapp:
- webapp_
    WebApp in Python Django recieves JSON format and logs to database.

To run the webapp for view only on http: 
```
    py manage.py runserver 192.168.137.1:80 
```

To run the webapp for datagathering on https: 
```
    py manage.py runserver_plus 192.168.137.1:443 --cert-file ../hereblewebapp/sslcert/localhost.crt --key-file ../herblewebapp/sslcert/localhost.key
```