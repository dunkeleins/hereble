#include <Arduino.h>
#include "BLEDevice.h"
#include <WiFi.h>
#include <HTTPClient.h>

#define SERVER_URL "http://your-server.com/api/bluetooth"
#define WIFI_SSID "your-SSID"
#define WIFI_PASSWORD "your-PASSWORD"
#define RSSI_THRESHOLD 10  // Mindeständerung, um eine Meldung zu senden
#define SCAN_TIME 5   // Sekunden, nach denen ein Gerät als verschwunden gilt

WiFiClient client;

class MyAdvertisedDeviceCallbacks : public BLEAdvertisedDeviceCallbacks {
    void onResult(BLEAdvertisedDevice advertisedDevice) {
        Serial.println("---------------");
        Serial.printf("MAC-Adresse: %s\n", advertisedDevice.getAddress().toString().c_str());
        Serial.printf("RSSI: %d dBm\n", advertisedDevice.getRSSI());

        // JSON-Daten vorbereiten
        String jsonPayload = "{";
        jsonPayload += "\"mac\":\"" + String(advertisedDevice.getAddress().toString().c_str()) + "\",";
        jsonPayload += "\"rssi\":" + String(advertisedDevice.getRSSI()) + ",";

        // Falls ein Gerätename vorhanden ist
        if (advertisedDevice.haveName()) {
            Serial.printf("Gerätename: %s\n", advertisedDevice.getName().c_str());
            jsonPayload += "\"name\":\"" + String(advertisedDevice.getName().c_str()) + "\",";
        }

        // Falls Service-UUIDs vorhanden sind
        if (advertisedDevice.haveServiceUUID()) {
            Serial.printf("Service-UUID: %s\n", advertisedDevice.getServiceUUID().toString().c_str());
            jsonPayload += "\"service_uuid\":\"" + String(advertisedDevice.getServiceUUID().toString().c_str()) + "\",";
        }

        // Falls Hersteller-Daten vorhanden sind
        if (advertisedDevice.haveManufacturerData()) {
            std::string manufacturerData = advertisedDevice.getManufacturerData();
            Serial.printf("Hersteller-Daten (HEX): ");
            
            String manufacturerDataHex = "";
            for (size_t i = 0; i < manufacturerData.length(); i++) {
                char hexByte[3];
                sprintf(hexByte, "%02X", manufacturerData[i]);
                manufacturerDataHex += hexByte;
                Serial.printf("%s ", hexByte);
            }
            Serial.println();

            jsonPayload += "\"manufacturer_data\":\"" + manufacturerDataHex + "\",";
        }

        // Letztes Komma entfernen, falls notwendig
        if (jsonPayload.endsWith(",")) {
            jsonPayload.remove(jsonPayload.length() - 1);
        }
        jsonPayload += "}";

        // Daten an Server senden
        sendToServer(jsonPayload);
        Serial.println("---------------");
    }
};

void sendToServer(String jsonPayload) {
    if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        http.begin(SERVER_URL);
        http.addHeader("Content-Type", "application/json");

        Serial.printf("Sende JSON: %s\n", jsonPayload.c_str());
        int httpResponseCode = http.POST(jsonPayload);
        Serial.printf("Server response: %d\n", httpResponseCode);
        http.end();
    }
}

void setup() {
    Serial.begin(115200);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Connecting to WiFi...");
    }
    Serial.println("Connected to WiFi");

    BLEDevice::init("");
}

void loop() {
    BLEScan* pBLEScan = BLEDevice::getScan();
    pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
    pBLEScan->setActiveScan(true);
    pBLEScan->start(SCAN_TIME, false);
}