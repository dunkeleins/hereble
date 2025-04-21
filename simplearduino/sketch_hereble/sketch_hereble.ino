#define DEBUG true

#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <Preferences.h>
#include <vector>
#include <algorithm>

BLEScan* pBLEScan;
String bleScanResults = "Keine BLE-Geräte gefunden";
int rssiThreshold;
Preferences preferences;

const int ledPin = 19;
const int buttonPin = 18;
bool ledOn = false;
bool bleFound = false;
unsigned long ledOffTime = 0;

// Funktionsprototypen
void bleScanTask(void * parameter);

void setup() {
    #if DEBUG
    Serial.begin(115200);
    #endif
    pinMode(ledPin, OUTPUT);
    digitalWrite(ledPin, LOW);
    pinMode(buttonPin, INPUT_PULLUP);

    preferences.begin("settings", false);
    rssiThreshold = preferences.getInt("rssiThreshold", -45);

    // CPU-Frequenz reduzieren
    //setCpuFrequencyMhz(80);

    // BLE Setup
    BLEDevice::init("");
    //esp_ble_tx_power_set(ESP_PWR_LVL_N6);
    //BLEDevice::setPower(ESP_PWR_LVL_P9);
    //ESP_PWR_LVL_N12 (power level -12 dBm)
    esp_ble_gap_config_local_privacy(true); // Rotiere lokale MAC
    pBLEScan = BLEDevice::getScan();
    pBLEScan->setActiveScan(false); // Passive Scans verbrauchen weniger Energie
    pBLEScan->setInterval(5); // Längeres Scan-Intervall
    pBLEScan->setWindow(100); // Kürzere Scan-Dauer
    
    xTaskCreatePinnedToCore(bleScanTask, "BLE_Scan_Task", 4096, NULL, 1, NULL, 0);
}

float calculateDistance(int rssi, int rssiAtOneMeter, float pathLossExponent) {
    return pow(10, (rssiAtOneMeter - rssi) / (10.0 * pathLossExponent));
}

void bleScanTask(void * parameter) {
    int referenceRSSI = -60;      // RSSI at 1 m distance
    float pathLossExponent = 2.0; // Enivronment (2 = open field, 3 = indoor, 4 = crowded)
    while (true) {
        BLEScanResults *foundDevices = pBLEScan->start(5, false);
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

        int deviceNr = 1;
        for (auto &device : devices) {
            bleScanResults += String(deviceNr) + ", ";
            bleScanResults += String(device.getRSSI()) + ", ";
            float distance = calculateDistance(device.getRSSI(), referenceRSSI, pathLossExponent);
            bleScanResults += String(distance) + " m";
            bleScanResults += "<br/>";
            deviceNr++;
        }

        if (devices.empty()) {
            bleScanResults = "Keine BLE-Geräte über der RSSI-Schwelle gefunden";
            bleFound = false;
        } else {
            bleScanResults = "Gefundene BLE-Geräte: " + String(deviceCount) + "<br/>" + bleScanResults;
            bleFound = true;
        }
        
        #if DEBUG
        Serial.println(bleScanResults);        
        #endif
        pBLEScan->clearResults();
        bleScanResults = "";
    }
}

void loop() {
    if (digitalRead(buttonPin) == LOW || bleFound) {
        if (digitalRead(buttonPin) == LOW) {
          ledOn = true;
          ledOffTime = millis() + 5000; // LED für 5 Sekunden aktivieren
        }
        digitalWrite(ledPin, HIGH);
    }
    
    if (ledOn && millis() > ledOffTime && !bleFound) {
        digitalWrite(ledPin, LOW);
        ledOn = false;
    }
    
    static unsigned long lastTime = 0;
    if (millis() - lastTime > 5000) { // Alle 5 Sekunden Geräte anzeigen
        lastTime = millis();
        #if DEBUG
        if (ledOn) Serial.println("LED ON");        
        if (!ledOn) Serial.println("LED OFF");        
        #endif
        
    }
}
