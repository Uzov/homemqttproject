#include <ArduinoJson.h>

#include "config.h"
#include "connections.h"
#include "cfgfile.h"

String clientName;

long lastReconnectAttempt = 0;
long lastMsg = 0;
int test_para = 10000;
unsigned long startMills;

//Объявление указателя на массив указателей relays на структуру relay
struct relay** relays = new relay*[n];

void setup() {
  for (int i = 0; i < n; i++) {
    switch (i) {
      case 0:
        relays[i] = &relay01;
        break;
      case 1:
        relays[i] = &relay02;
        break;
      case 2:
        relays[i] = &relay03;
        break;
      case 3:
        relays[i] = &relay04;
        break;
    }
  }

  pinMode(BUILTIN_LED, OUTPUT);
  digitalWrite(BUILTIN_LED, HIGH);
  Serial.begin(115200);
  Serial.println();
  startMills = millis();

  for (int i = 0; i < n; i++) {
    pinMode(relays[i]->relayPin, OUTPUT);
  }

  wifi_connect();
  delay(500);

  getTime();
  delay(500);

  loadcerts();
  delay(500);

  getBme280();
  delay(500);

  //Configure secure client connection
  //wifiClient.setTrustAnchors(&caCertX509); /* Load CA cert into trust store */
  //wifiClient.allowSelfSignedCerts(); /* Enable self-signed cert support */
  wifiClient.setFingerprint(fingerprint); /* Load SHA1 mqtt cert fingerprint for connection validation */

#ifdef TLS_DEBUG
  //Call verifytls to verify connection can be done securely and validated -
  //this is optional but was useful during debug
  verifytls();
#endif

  client.setCallback(subCallback);

  clientName += "esp12F-";
  uint8_t mac[6];
  WiFi.macAddress(mac);
  clientName += macToStr(mac);
  clientName += "-";
  clientName += String(micros() & 0xff, 16);
  //Connect to MQTT broker
  reconnect(clientName);

  for (int i = 0; i < n; i++) {
    if (loadConfig(relays, i)) {
      if (String(relays[i]->relayState) == "OFF") {
        digitalWrite(relays[i]->relayPin, LOW);
        String mqttMsg = "{\"" + messageType[2] + "\":\"OFF\",";
        mqttMsg += "\"RELAY\":\"";
        mqttMsg += String(relays[i]->relayNum) + "\"}";
        Serial.println(mqttMsg);
        sendmqttMsg(outTopic, &mqttMsg);
      } else if (String(relays[i]->relayState) == "ON") {
        digitalWrite(relays[i]->relayPin, HIGH);
        String mqttMsg = "{\"" + messageType[2] + "\":\"ON\",";
        mqttMsg += "\"RELAY\":\"";
        mqttMsg += String(relays[i]->relayNum) + "\"}";
        Serial.println(mqttMsg);
        sendmqttMsg(outTopic, &mqttMsg);
      } else {
        Serial.println("Incorrect relay " + String(relays[i]->relayName) + " initial state: " + String(relays[i]->relayState));
      }
    }
  }
}

//Receive MQTT message
void subCallback(char *inTopic, byte *payload, unsigned int length) {
  String message;

  DynamicJsonDocument doc(256);

#ifdef SERIAL_DEBUG
  Serial.print("Message arrived in topic: ");
  Serial.println(inTopic);
  Serial.print("Message:");
#endif
  for (int i = 0; i < length; i++) {
    message = message + ((char)payload[i]);
  }
#ifdef SERIAL_DEBUG
  Serial.println(message);
  Serial.println(" ===> Received ok!");
#endif
  auto error = deserializeJson(doc, (const byte*)payload, length);
  if (error) {
    Serial.println("Failed to deserialize received data!");
  }
  doc.shrinkToFit();
  const char* command = "ERROR";
  int relayPin;
  const char* relayNum = "ERROR";
  int i;

  if (doc.containsKey(messageType[0])) {
    command = doc[messageType[0]];
  }

  if (doc.containsKey(messageType[0]) && doc.containsKey("RELAY")) {
    command = doc[messageType[0]];
    for (int j = 0; j < n; j++) {
      
      // Int j to char jToStr conversion 
      char jToStr[sizeof(int)];
      sprintf(jToStr, "0%d", (j+1));
      if (strcmp(doc["RELAY"], (char*)jToStr) == 0) {
        i = j;
        relayPin = (int)relays[i]->relayPin;
        relayNum = doc["RELAY"];
       }
    }
  }

  if ((strcmp(command, cmd1) == 0) && (digitalRead(relayPin) == LOW) && !(relayNum == "ERROR")) {
    digitalWrite(relayPin, HIGH);
    relays[i]->relayState = cmd1;
    saveConfig(relays[i]);
    if (digitalRead(relayPin) == HIGH) {
      String mqttMsg = "{\"" + messageType[3] + "\":\"" + command + "\",";
      mqttMsg += "\"RELAY\":\"" + String(relayNum) + "\"}";
      sendmqttMsg(outTopic, &mqttMsg);
#ifdef SERIAL_DEBUG
      Serial.println("Relay" + String(relayNum) + " is switched on!");
#endif
    }
  } else if ((strcmp(command, cmd1) == 0) && (digitalRead(relayPin) == HIGH) && !(relayNum == "ERROR")) {
    String mqttMsg = "{\"" + messageType[4] + "\":\"" + command + "_ALREADY\",";
    mqttMsg += "\"RELAY\":\"" + String(relayNum) + "\"}";
    sendmqttMsg(outTopic, &mqttMsg);
  } else if ((strcmp(command, cmd2) == 0) && (digitalRead(relayPin) == HIGH) && !(relayNum == "ERROR")) {
    digitalWrite(relayPin, LOW);
    relays[i]->relayState = cmd2;
    saveConfig(relays[i]);
    if (digitalRead(relayPin) == LOW) {
      String mqttMsg = "{\"" + messageType[3] + "\":\"" + command + "\",";
      mqttMsg += "\"RELAY\":\"" + String(relayNum) + "\"}";
      sendmqttMsg(outTopic, &mqttMsg);
#ifdef SERIAL_DEBUG
      Serial.println("Relay" + String(relayNum) + " is switched off!");
#endif
    }
  } else if ((strcmp(command, cmd2) == 0) && (digitalRead(relayPin) == LOW) && !(relayNum == "ERROR")) {
    String mqttMsg = "{\"" + messageType[4] + "\":\"" + command + "_ALREADY\",";
    mqttMsg += "\"RELAY\":\"" + String(relayNum) + "\"}";
    sendmqttMsg(outTopic, &mqttMsg);
  } else if (strcmp(command, cmd3) == 0) {
    String mqttMsg;
    serializeValues(id, &mqttMsg, command);
    sendmqttMsg(outTopic, &mqttMsg);
  } else {
    Serial.println("Unknown command!");
    String mqttMsg = "{\"" + messageType[4] + "\":\"UNKNOWN_COMMAND\"}";
    sendmqttMsg(outTopic, &mqttMsg);
  }
}

//Serialize message payload as json
void serializeValues(String sensorID, String* json, String command) {
  DynamicJsonDocument doc(256);
  doc[messageType[1]] = command;
  doc["sensorID"] = sensorID;
  doc["temperature"] = floor(bme.readTemperature() * 100) / 100;
  doc["press_hpa"] = floor((bme.readPressure() / 100.0F) * 100) / 100;
  doc["press_mmhg"] = floor((bme.readPressure() * 0.00750062) * 100) / 100;
  doc["altitude"] = floor(bme.readAltitude(SEALEVELPRESSURE_HPA) * 100) / 100;
  doc["humidity"] = floor(bme.readHumidity() * 100) / 100;

  for (int i = 0; i < n; i++) {
    if (digitalRead(relays[i]->relayPin) == LOW) {
      doc[String(relays[i]->relayName)] = "OFF";
    } else if (digitalRead(relays[i]->relayPin) == HIGH) {
      doc[String(relays[i]->relayName)] = "ON";
    }
  }

  auto bytesWritten = serializeJson(doc, *json);
  if (bytesWritten != 0) {
    Serial.println("Successfully serialized data to send, number of bytes written: " + String(bytesWritten));
  } else {
    Serial.println("Failed to serialize data to send");
  }
  doc.shrinkToFit();
}

//Send MQTT message
void sendmqttMsg(char* topictosend, String* payload) {

  if (client.connected()) {
#ifdef SERIAL_DEBUG
    Serial.print("Sending payload: ");
    Serial.print(*payload);
#endif

    unsigned int msg_length = payload->length();

#ifdef SERIAL_DEBUG
    Serial.print(" length: ");
    Serial.print(msg_length);
    Serial.print(" ===> ");
#endif

    byte* p = (byte*)malloc(msg_length);
    memcpy(p, (char*) payload->c_str(), msg_length);

    if (client.publish(topictosend, p, msg_length)) {
#ifdef SERIAL_DEBUG
      Serial.println("Publish ok!");
#endif
      free(p);
    } else {
#ifdef SERIAL_DEBUG
      Serial.println("Publish failed!");
#endif
      free(p);
    }
  }
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    if (!client.connected()) {
      long now = millis();
      if (now - lastReconnectAttempt > 2000) {
        lastReconnectAttempt = now;
        if (reconnect(clientName)) {
          lastReconnectAttempt = 0;
        }
      }
    } else {
      long now = millis();
      if (now - lastMsg > test_para) {
        lastMsg = now;
      }
      client.loop();
    }
  } else {
    wifi_connect();
  }
}
