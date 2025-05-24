#define DEBUG false // Set to true for debugging output in writeLog()

#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <Preferences.h>
#include <vector>
#include <algorithm>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "mbedtls/sha256.h"
#include "constants_ble.h"

/*
Das ist ein einfaches Arduino-Sketch zum Scannen von BLE-Geräten und Senden ihrer Daten an einen Server.
Dieses Beispiel verwendet die ESP32-Bibliotheken für BLE, WiFi und HTTP-Client.

Damit dieser Sketch funktioniert, muss die Datei "constants_ble.h" im selben Verzeichnis wie dieses Sketch liegen.
constants_ble.h:
const char* ssid = "xxxx";
const char* password = "xxxx";
const char* serverUrl = "https://ip.ip.ip.ip/sendbledata/";
const char* salt = "salt"; 
const char* root_ca = \
"-----BEGIN CERTIFICATE-----\n" \
"MIID...Certificate... \n" \
"-----END CERTIFICATE-----\n";
*/

// Globale Variablen
BLEScan* pBLEScan;
String bleScanResults = "Keine BLE-Geräte gefunden";
int rssiThreshold;
Preferences preferences;
bool ledOn = false;
bool bleFound = false;
bool realLED = false;
unsigned long ledOffTime = 0;
int iNachlauf = 5000; // Nachlaufzeit in Millisekunden

// ESP32 Pin Konfiguration
const int ledPin = 21;
const int buttonPin = 36;

// Funktionsprototypen
void bleScanTask(void * parameter);

// Funktion zum Hashen der MAC-Adresse mit SHA-256 und Salt
String hashMacAddress(const String& mac) {
  // SHA-256 Hash berechnen
  byte shaResult[32]; // 256 Bit = 32 Byte
  mbedtls_sha256_context ctx;
  mbedtls_sha256_init(&ctx);
  mbedtls_sha256_starts(&ctx, 0); // 0 = SHA-256 (nicht SHA-224)

  String combined = mac + salt;

  // In Byte-Array umwandeln
  const char* combined_cstr = combined.c_str();

  // MAC + Salt hinzufügen
  mbedtls_sha256_update(&ctx, (const unsigned char*)combined_cstr, strlen(combined_cstr));
  mbedtls_sha256_finish(&ctx, shaResult);
  mbedtls_sha256_free(&ctx);

  // Hex-String zurückgeben
  String hashString = "";
  for (int i = 0; i < 32; i++) {
    if (shaResult[i] < 16) hashString += "0";
    hashString += String(shaResult[i], HEX);
  }
  return hashString;
}

// Funktion zum Schreiben von Log-Nachrichten auf der seriellen Konsole
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
    rssiThreshold = preferences.getInt("rssiThreshold", -150);
    rssiThreshold = -150;

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
    // CPU-Frequenz reduzieren, keine Verbesserung beim Energiebedarf, daher auskommentiert
    //setCpuFrequencyMhz(80);

    // BLE Setup
    BLEDevice::init("");
    BLEDevice::setPower(ESP_PWR_LVL_P20); // ESP32-S3 HighPower 20dbm
    esp_ble_gap_config_local_privacy(true); // MAC-Randomisierung aktivieren
    pBLEScan = BLEDevice::getScan();
    pBLEScan->setActiveScan(true); // Passive Scans verbrauchen weniger Energie, Active Scans finden mehr Geräte, daher auf true setzen
    pBLEScan->setInterval(5000); // Scan-Intervall verbressert die anzahl der gefundenen Geräte
    pBLEScan->setWindow(4999); // Scan-Dauer
    
    xTaskCreatePinnedToCore(bleScanTask, "BLE_Scan_Task", 4096, NULL, 1, NULL, 0);
}

float calculateDistance(int rssi, int rssiAtOneMeter, float pathLossExponent) {
    return pow(10, (rssiAtOneMeter - rssi) / (10.0 * pathLossExponent));
}

void bleScanTask(void * parameter) {
    int referenceRSSI = -140;      // RSSI 60 entspricht ca. 1 Meter Entfernung; für Testzwecke anpassen
    float pathLossExponent = 2.0; // Umgebung für die Berechnung der Distanz (2 = open field, 3 = indoor, 4 = crowded)
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
        // Ergebnisse formatieren
        bleScanResults = "";
        for (auto &device : devices) {
            bleScanResults += String(deviceNr) + ", ";
            bleScanResults += String(device.getRSSI()) + ", ";
            float distance = calculateDistance(device.getRSSI(), referenceRSSI, pathLossExponent);
            bleScanResults += String(distance) + " m";
            bleScanResults += "<br/>";

            // JSON-Daten für jedes Gerät erstellen
            JsonObject jsonDevice = jsonDevices.createNestedObject();
            jsonDevice["mac"] = "";
            jsonDevice["mac_hash"] = hashMacAddress(device.getAddress().toString().c_str()); 
            jsonDevice["rssi"] = device.getRSSI();
            jsonDevice["name"] = device.getName().c_str();
            jsonDevice["distance"] = calculateDistance(device.getRSSI(), referenceRSSI, pathLossExponent);
            jsonDevice["service_uuid"] = device.getServiceUUID().toString().c_str();
            jsonDevice["manufacturer_data"] = "";
            jsonDevice[""] = "";

            deviceNr++;
        }

        // JSON-Dokument vorbereiten
        String json;
        serializeJson(doc, json);

        // JSON-Daten an den Server senden
        if (WiFi.status() == WL_CONNECTED) {
            WiFiClientSecure client;
            client.setCACert(root_ca);  // Für verifizierte Verbindung

            HTTPClient https;
            https.begin(client, serverUrl);
            https.addHeader("Content-Type", "application/json");
            int httpResponseCode = https.POST(json);
            #if DEBUG
            Serial.print("HTTP Response code: ");
            Serial.println(httpResponseCode);
            #endif
            Serial.println(json);
            https.end();
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

// Hauptprogramm
void loop() {
    // Button Logik
    if (digitalRead(buttonPin) == LOW || bleFound) {
        ledOn = true;
        ledOffTime = millis() + iNachlauf; // Wartezeit bis wieder ausgeschaltet werden soll (Nachlauf)
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
            if (realLED) Serial.println("LED ON");        
            if (!realLED) Serial.println("LED OFF");        
        #endif
        
    }
    // Kurze Pause, um den Energieverbrauch zu reduzieren
    delay(1000);
}
