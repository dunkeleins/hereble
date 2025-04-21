#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <WebSocketsServer.h>
#include <esp_wifi.h>
#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <esp_gap_ble_api.h>

const char* ssid = "HereBLE";
const char* password = "12345678";

IPAddress local_IP(192, 168, 221, 1);
IPAddress gateway(192, 168, 221, 1);
IPAddress subnet(255, 255, 255, 0);
IPAddress client_IP(192, 168, 221, 100);

AsyncWebServer server(80);
WebSocketsServer webSocket(81);
BLEScan* pBLEScan;
String bleScanResults = "Keine BLE-Geräte gefunden";
int rssiThreshold = -80;

const int ledPin = 19;

// Funktionsprototypen
void webSocketEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length);
void bleScanTask(void * parameter);
void printConnectedDevices();

void setup() {
    Serial.begin(115200);
    pinMode(ledPin, OUTPUT);
    digitalWrite(ledPin, LOW);

    WiFi.softAP(ssid, password);
    WiFi.softAPConfig(local_IP, gateway, subnet);
    WiFi.setTxPower(WIFI_POWER_19_5dBm); // Sendeleistung reduzieren, da maximal ein client verbindet
    Serial.println("Access Point gestartet");
    Serial.print("IP-Adresse: ");
    Serial.println(WiFi.softAPIP());

    server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
        request->send_P(200, "text/html", R"rawliteral(
        <!DOCTYPE html>
        <html>
        <head>
            <script>
                var socket = new WebSocket("ws://" + location.hostname + ":81");
                function sendRSSI() {
                    var rssiValue = document.getElementById("rssi").value;
                    socket.send(rssiValue);
                }
                socket.onmessage = function(event) {
                    document.getElementById("output").innerHTML = event.data;
                };
            </script>
            <title>HereBLE</title>
        </head>
        <body>
            <h2>ESP32 Live Output</h2>
            <p id="output">Warten auf Daten...</p>
            <label for="rssi">RSSI Schwelle: </label>
            <input type="number" id="rssi" value="-80">
            <button onclick="sendRSSI()">Setzen</button>
        </body>
        </html>
        )rawliteral");
    });

    server.begin();
    webSocket.begin();
    webSocket.onEvent(webSocketEvent);

    // CPU-Frequenz reduzieren
    setCpuFrequencyMhz(80);

    // BLE Setup
    BLEDevice::init("");
    esp_ble_gap_config_local_privacy(true); // BLE Privacy aktivieren
    pBLEScan = BLEDevice::getScan();
    pBLEScan->setActiveScan(false); // Passive Scans verbrauchen weniger Energie
    pBLEScan->setInterval(5);  // Längeres Scan-Intervall
    pBLEScan->setWindow(100);    // Kürzere Scan-Dauer
    
    xTaskCreatePinnedToCore(bleScanTask, "BLE_Scan_Task", 4096, NULL, 1, NULL, 0);
}

void webSocketEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length) {
    if (type == WStype_TEXT) {
        String message = String((char*)payload);
        rssiThreshold = message.toInt();
        Serial.printf("Neue RSSI-Schwelle: %d\n", rssiThreshold);
    }
}

void printConnectedDevices() {
    wifi_sta_list_t wifi_sta_list;
    esp_wifi_ap_get_sta_list(&wifi_sta_list);

    for (int i = 0; i < wifi_sta_list.num; i++) {
        wifi_sta_info_t station = wifi_sta_list.sta[i];
        Serial.printf("Gerät verbunden: %02X:%02X:%02X:%02X:%02X:%02X\n", 
                      station.mac[0], station.mac[1], station.mac[2], 
                      station.mac[3], station.mac[4], station.mac[5]);
    }
}

void bleScanTask(void * parameter) {
    while (true) {
        Serial.println("Starte BLE-Scan...");
        BLEScanResults *foundDevices = pBLEScan->start(5, false);
        int deviceCount = foundDevices->getCount();
        Serial.printf("%d BLE-Geräte gefunden\n", deviceCount);
        
        bool deviceFound = false;
        bleScanResults = "Gefundene BLE-Geräte: " + String(deviceCount) + "<br/>";
        for (int i = 0; i < deviceCount; i++) {
            BLEAdvertisedDevice device = foundDevices->getDevice(i);
            if (device.getRSSI() >= rssiThreshold) {
                bleScanResults += device.getAddress().toString().c_str();
                bleScanResults += " (RSSI: ";
                bleScanResults += String(device.getRSSI());
                bleScanResults += "), ";
                if (device.haveName()) {
                  bleScanResults += String(device.getName().c_str()) + ", ";
                }
                if (device.haveServiceUUID()) {
                  bleScanResults += String(device.getServiceUUID().toString().c_str());
                }
                bleScanResults += "<br/>";
                deviceFound = true;
            }
        }
        
        if (!deviceFound) {
            bleScanResults = "Keine BLE-Geräte über der RSSI-Schwelle gefunden";
            digitalWrite(ledPin, LOW);
        } else {
            digitalWrite(ledPin, HIGH);
        }
        
        webSocket.broadcastTXT(bleScanResults);
        pBLEScan->clearResults();
        
        //esp_light_sleep_start(); // Light Sleep aktivieren
    }
}

void loop() {
    webSocket.loop();
    static unsigned long lastTime = 0;
    if (millis() - lastTime > 5000) { // Alle 5 Sekunden Geräte anzeigen
        lastTime = millis();
        Serial.println("Überprüfung der verbundenen Geräte...");
        printConnectedDevices();
    }
}