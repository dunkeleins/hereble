# hereble
Bluetooth Low Energy ESP32 Beacon collects data and sends to central service.

herebleesp:
ESP32 program to setup a webservice which can be connected with a borwser to see scanned BLE devices in range.

hereblewebapp:
Virtual python environment for the webapp django installation.

simplearduino:
- sketch_herble:
    ESP32 program to scan for BLE devices and send information on serial output.
- sketch_herble_simple_nb:
    ESP32 program to send BLE informations in JSON format to a http service.

webapp:
WebApp in Python Django recieves JSON format and logs to database.