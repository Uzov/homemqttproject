#ifndef	_CONFIG_H_
#define	_CONFIG_H_

#define RELAY01_PIN D1
#define RELAY02_PIN D1
#define RELAY03_PIN D1
#define RELAY04_PIN D1

#define SERIAL_DEBUG
#define TLS_DEBUG

#define SDA D5
#define SCL D6
#define SEALEVELPRESSURE_HPA (1013.25)

// Insert your FQDN of your MQTT Broker
#define MQTT_SERVER "192.168.35.113"
#define SNTP_SERVER "ru.pool.ntp.org"
const char* mqtt_server = MQTT_SERVER;
const char* sntp_server = SNTP_SERVER;

// WiFi Credentials
const char* ssid = "********";
const char* password = "********";
const char* mqtt_user = "********";
const char* mqtt_password = "********";

// Static IP configuration
byte ip_static[] = { 192, 168, 20, 130 };
byte ip_gateway[] = { 192, 168, 20, 1 };
byte ip_subnet[] = { 255, 255, 255, 0 };
byte ip_dns[] = { 192, 168, 20, 1 };

//Sensor ID
String id = "20.130";

// outTopics and inTopics
char* outTopic = "/home/20.130/out";
char* inTopic = "/home/20.130/in";

String messageType[5] = { "CMD", "ANSW", "SYNCH", "SUCCESS", "ERROR" };
const char *cmd1 = "ON";
const char *cmd2 = "OFF";
const char *cmd3 = "GET_DATA";

// Fingerprint of the broker CA
// openssl x509 -in  mqttserver.crt -sha1 -noout -fingerprint
const char* fingerprint = "**********************************************";

struct relay {
  const char* relayName;
  unsigned short relayPin: 4;
  const char* relayNum;
  const char* relayState;
};

//Количество реле, но не больше 4-х. Больше можно, но надо тогда увеличить количество переменных struct relay relay0n (см. ниже). 
const int n = 1;

struct relay relay01 = { "RELAY01", RELAY01_PIN, "01", "NONE" };
struct relay relay02 = { "RELAY02", RELAY02_PIN, "02", "NONE" };
struct relay relay03 = { "RELAY03", RELAY03_PIN, "03", "NONE" };
struct relay relay04 = { "RELAY04", RELAY04_PIN, "04", "NONE" };

#endif
