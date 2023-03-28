#ifndef  _CFGFILE_H_
#define _CFGFILE_H_

#include "FS.h"
#include "config.h"

// Массив для хранения считанных из конфигурационного файла данных
const char* initRelayState[n][3];

bool openConfigFile() {
  char intToStr[1];

  if (!SPIFFS.begin()) {
    Serial.println("Failed to mount file system.");
    return false;
  }

  File configFile = SPIFFS.open("/config.json", "r");
  if (!configFile) {
    Serial.println("Failed to open config file.");
    configFile.close();
    return false;
  }

  size_t size = configFile.size();
  if (size > 1024) {
    Serial.println("Config file size is too large.");
    configFile.close();
    return false;
  }

  // Allocate a buffer to store contents of the file.
  std::unique_ptr<char[]> buf(new char[size]);
  configFile.readBytes(buf.get(), size);

  // StaticJsonDocument<200> _doc;
  DynamicJsonDocument _doc(256);

  auto error = deserializeJson(_doc, buf.get());
  if (error) {
    Serial.println("Failed to parse config file.");
    configFile.close();
    return false;
  }

  for (int i = 0; i < n; i++) {
    sprintf(intToStr, "%d", (i + 1));
    initRelayState[i][3] = ((const char*) _doc[("RELAY0" + String(intToStr))]);
  }
  configFile.close();
  return true;
}

bool loadConfig(struct relay** _relays, int i) {
  char intToStr[1];
  if (openConfigFile()) {
    sprintf(intToStr, "%d", (i + 1));
    _relays[i]->relayState = initRelayState[i][3];
#ifdef SERIAL_DEBUG
      Serial.print("Loaded relay 0" + String(intToStr) + " state after config file read: ");
      Serial.println(_relays[i]->relayState);
#endif
    return true;
  } else {
    return false;
  }
}

bool saveConfig(struct relay *_relay) {
  char intToStr[1];
  const char* str;
  if (openConfigFile()) {
    // StaticJsonDocument<200> _doc;
    DynamicJsonDocument _doc(256);
  
    for (int i = 0; i < n; i++) {
      sprintf(intToStr, "%d", (i + 1));
      //Serial.println(initRelayState[i][3]);
      _doc[("RELAY0" + String(intToStr))] = String(initRelayState[i][3]);
      if (String(_relay->relayName) == ("RELAY0" + String(intToStr))) {
        _doc["RELAY" + String(_relay->relayNum)] = _relay->relayState;
        str = _doc[("RELAY" + String(_relay->relayNum))];
        #ifdef SERIAL_DEBUG     
          Serial.print("Write to config file ===> ");
          Serial.print("\"RELAY" + String(_relay->relayNum) + "\"");
          Serial.print(": ");
          Serial.println("\"" + String(str) + "\"");
        #endif
      }
    }
  
    if (!SPIFFS.begin()) {
      Serial.println("Failed to mount file system.");
      return false;
    }
  
    File configFile = SPIFFS.open("/config.json", "w");
    if (!configFile) {
      Serial.println("Failed to open config file for writing");
      return false;
    }
  
    serializeJson(_doc, configFile);
    
    configFile.close();
    return true;
  } else {
    return false;
  }
}

#endif
