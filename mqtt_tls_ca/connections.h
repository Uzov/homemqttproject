#ifndef	_CONNECTIONS_H_
#define	_CONNECTIONS_H_

#include <FS.h>
#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
// Arduino client for MQTT
#include <PubSubClient.h>
#include <time.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>

#include "config.h"

Adafruit_BME280 bme;
TwoWire Wire2;

WiFiClientSecure wifiClient;
PubSubClient client(mqtt_server, 8883, wifiClient);

// Use WiFiClientSecure class to create TLS connection
void verifytls()
{
  Serial.print("Verifying TLS connection to ");
  Serial.println(mqtt_server);
  if (!wifiClient.connect(mqtt_server, 8883)) {
    Serial.println("connection failed");
    return;
  }

  if (wifiClient.verify(fingerprint, mqtt_server)) {
    Serial.println("Certificate matches");
  } else {
    Serial.println("Certificate doesn't match");
  }
}

// Load Certificates
void loadcerts()
{
  if (!SPIFFS.begin()) {
    Serial.println("Failed to mount file system");
    return;
  }

  // Load CA file from SPIFFS
  File ca = SPIFFS.open("/ca.crt.der", "r"); //uploaded file name
  if (!ca) {
    Serial.println("Failed to open ca ");
  } else {
    Serial.println("Success to open ca");
    // Set server CA file
    if (wifiClient.loadCACert(ca)) {
      Serial.println("ca loaded");
    } else {
      Serial.println("ca failed");
    }
  }
}

// Synchronize time using SNTP. This is necessary to verify that
// the TLS certificates offered by the server are currently valid.
void getTime()
{
  Serial.print("Setting time using SNTP");
  configTime(8 * 3600, 0, mqtt_server, sntp_server);
  time_t now = time(nullptr);
  while (now < 1000) {
    delay(500);
    Serial.print(".");
    if (digitalRead(BUILTIN_LED) == HIGH) {
        digitalWrite(BUILTIN_LED, LOW);
        } else {
          digitalWrite(BUILTIN_LED, HIGH);
        }
    now = time(nullptr);
  }
  Serial.println("");
  struct tm timeinfo;
  gmtime_r(&now, &timeinfo);
  Serial.print("Current time: ");
  Serial.print(asctime(&timeinfo));
}


void getBme280()
{
  unsigned status;
  
  Wire2.begin(SDA, SCL, 100000);
  status = bme.begin(0x76, &Wire2);
  if (!status) {
    Serial.println("Could not find a valid BME280 sensor, check wiring, address, sensor ID!");
  } else {
    Serial.print("BME sensorID was: 0x"); Serial.println(bme.sensorID(), 16);
    }
  bme.setSampling(Adafruit_BME280::MODE_NORMAL,
                  Adafruit_BME280::SAMPLING_X16, // temperature
                  Adafruit_BME280::SAMPLING_X16, // pressure
                  Adafruit_BME280::SAMPLING_X16, // humidity
                  Adafruit_BME280::FILTER_OFF);               
}

//Connect to MQTT Broker.
boolean reconnect(String clientName)
{
  String message;
  while (!client.connected()) {
#ifdef SERIAL_DEBUG
    Serial.print("Attempting MQTT broker connection...");
#endif
    if (client.connect((char*) clientName.c_str(), mqtt_user, mqtt_password)) {
#ifdef SERIAL_DEBUG
      Serial.println("===> " + clientName + " mqtt connected");
#endif
      message = "Sensor " + id + ", client name " + clientName + " connected";
      unsigned int msg_length = message.length();
      byte* p = (byte*)malloc(msg_length);
      memcpy(p, (char*) message.c_str(), msg_length);
      client.publish(outTopic, p, msg_length);
      client.subscribe(inTopic);
      digitalWrite(BUILTIN_LED, LOW);
    } else {
#ifdef SERIAL_DEBUG
      Serial.print("---> mqtt failed, rc=");
      Serial.print(client.state());
      Serial.println(". Trying again in 3 seconds...");
#endif
      digitalWrite(BUILTIN_LED, HIGH);
      delay(3000);
    }
  }
  return client.connected();
}


//Connect to WiFi
void wifi_connect()
{
  if (WiFi.status() != WL_CONNECTED) {

  #ifdef SERIAL_DEBUG
    Serial.println();
    Serial.print("===> WIFI ---> Connecting to ");
    Serial.println(ssid);
  #endif

    delay(10);
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    WiFi.config(IPAddress(ip_static), IPAddress(ip_gateway), IPAddress(ip_subnet), IPAddress(ip_dns));

    int Attempt = 0;
    while (WiFi.status() != WL_CONNECTED) {
      Serial.print(". ");
      delay(1000);
      if (digitalRead(BUILTIN_LED) == HIGH) {
        digitalWrite(BUILTIN_LED, LOW);
        } else {
          digitalWrite(BUILTIN_LED, HIGH);
        }
      
      Attempt++;
      if (Attempt == 150)
      {
        Serial.println();
        Serial.println("-----> Could not connect to WIFI");

        ESP.restart();
        delay(200);
      }

    }
    #ifdef SERIAL_DEBUG
      Serial.println();
      Serial.print("===> WiFi connected");
      Serial.print(" ------> IP address: ");
      Serial.println(WiFi.localIP());
    #endif
  }
}

String macToStr(const uint8_t* mac)
{
  String result;
  for (int i = 0; i < 6; ++i) {
    result += String(mac[i], 16);
    if (i < 5)
      result += ':';
  }
  return result;
}
#endif
