#define DEBUG true

#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <Preferences.h>
#include <vector>
#include <algorithm>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

BLEScan* pBLEScan;
String bleScanResults = "Keine BLE-Geräte gefunden";
int rssiThreshold;
Preferences preferences;

const int ledPin = 21;
const int buttonPin = 36;
bool ledOn = false;
bool bleFound = false;
bool realLED = false;
unsigned long ledOffTime = 0;

const char* ssid = "hereble";
const char* password = "123456789012";
const char* serverUrl = "http://192.168.137.1/sendbledata/";

// Funktionsprototypen
void bleScanTask(void * parameter);

void writeLog(String msg) {
  if (msg != "") {
    Serial.println(String(millis()) + " " + msg);
  }
}

void setup() {
    #if DEBUG
    Serial.begin(115200);
    #endif
    pinMode(ledPin, OUTPUT);
    digitalWrite(ledPin, HIGH);
    pinMode(buttonPin, INPUT_PULLUP);

    preferences.begin("settings", false);
    rssiThreshold = preferences.getInt("rssiThreshold", -40);
    rssiThreshold = -200;

    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
      delay(500);
      #if DEBUG
      Serial.print(".");
      #endif
    }

    #if DEBUG
    Serial.println("");
    Serial.print("Connected to WiFi. IP address: ");
    Serial.println(WiFi.localIP());
    #endif
    // CPU-Frequenz reduzieren
    //setCpuFrequencyMhz(80);

    // BLE Setup
    BLEDevice::init("");
    BLEDevice::setPower(ESP_PWR_LVL_P20); // ESP32-S3 HighPower 20dbm
    esp_ble_gap_config_local_privacy(true); // Rotiere lokale MAC
    pBLEScan = BLEDevice::getScan();
    pBLEScan->setActiveScan(true); // Passive Scans verbrauchen weniger Energie, Active Scans finden mehr Geräte
    pBLEScan->setInterval(5000); // Scan-Intervall
    pBLEScan->setWindow(4999); // Scan-Dauer
    
    xTaskCreatePinnedToCore(bleScanTask, "BLE_Scan_Task", 4096, NULL, 1, NULL, 0);
}

float calculateDistance(int rssi, int rssiAtOneMeter, float pathLossExponent) {
    return pow(10, (rssiAtOneMeter - rssi) / (10.0 * pathLossExponent));
}

void bleScanTask(void * parameter) {
    int referenceRSSI = -60;      // RSSI at 1 m distance
    float pathLossExponent = 2.0; // Enivronment (2 = open field, 3 = indoor, 4 = crowded)
    while (true) {
        BLEScanResults *foundDevices = pBLEScan->start(1, false); // 0 unendlich langer Scan, blockiert den Thread
        int deviceCount = 0;

        std::vector<BLEAdvertisedDevice> devices;
        for (int i = 0; i < foundDevices->getCount(); i++) {
            BLEAdvertisedDevice device = foundDevices->getDevice(i);
            if (device.getRSSI() >= rssiThreshold) {
                devices.push_back(device);
                deviceCount++;
            }
        }

        std::sort(devices.begin(), devices.end(), [](BLEAdvertisedDevice &a, BLEAdvertisedDevice &b) {
            return a.getRSSI() > b.getRSSI();
        });

        DynamicJsonDocument doc(2048);
        JsonArray jsonDevices = doc.createNestedArray("devices");

        int deviceNr = 1;
        for (auto &device : devices) {
            bleScanResults += String(deviceNr) + ", ";
            bleScanResults += String(device.getRSSI()) + ", ";
            float distance = calculateDistance(device.getRSSI(), referenceRSSI, pathLossExponent);
            bleScanResults += String(distance) + " m";
            bleScanResults += "<br/>";

                        
            JsonObject jsonDevice = jsonDevices.createNestedObject();
            jsonDevice["mac"] = device.getAddress().toString().c_str();
            jsonDevice["rssi"] = device.getRSSI();
            jsonDevice["name"] = device.getName().c_str();
            jsonDevice["distance"] = calculateDistance(device.getRSSI(), referenceRSSI, pathLossExponent);
            jsonDevice["service_uuid"] = device.getServiceUUID().toString().c_str();
            jsonDevice["manufacturer_data"] = "";

            deviceNr++;
        }

        String json;
        serializeJson(doc, json);

        if (WiFi.status() == WL_CONNECTED) {
            HTTPClient http;
            http.begin(serverUrl);
            http.addHeader("Content-Type", "application/json");
            int httpResponseCode = http.POST(json);
            #if DEBUG
            Serial.print("HTTP Response code: ");
            Serial.println(httpResponseCode);
            #endif
            Serial.println(json);
            http.end();
        } else {
            #if DEBUG
            Serial.println("WiFi not connected");
            #endif
        }

        if (devices.empty()) {
            //bleScanResults = "Keine BLE-Geräte über der RSSI-Schwelle gefunden";
            bleFound = false;
        } else {
            bleScanResults = "Gefundene BLE-Geräte: " + String(deviceCount) + "<br/>" + bleScanResults;
            bleFound = true;
        }
        
        #if DEBUG
        //Serial.println(bleScanResults);
        writeLog(bleScanResults);        
        #endif
        pBLEScan->clearResults();
        bleScanResults = "";
        delay(500);
    }
}

void loop() {
    // Button Logik
    if (digitalRead(buttonPin) == LOW || bleFound) {
        ledOn = true;
        ledOffTime = millis() + 5000; // Wartezeit bis wieder ausgeschaltet werden soll (Nachlauf)
        digitalWrite(ledPin, LOW);
        realLED = true;
    }
    
    if (ledOn && millis() > ledOffTime && !bleFound) {
        digitalWrite(ledPin, HIGH);
        ledOn = false;
        realLED = false;
    }
    
    static unsigned long lastTime = 0;
    if (millis() - lastTime > 5000) { // Alle 5 Sekunden Geräte anzeigen
        lastTime = millis();
        #if DEBUG
        //if (realLED) Serial.println("LED ON");        
        //if (!realLED) Serial.println("LED OFF");        
        #endif
        
    }
    delay(1000);
}
