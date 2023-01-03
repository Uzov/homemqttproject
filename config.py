import os.path

certificates_path = "/home/pi/mosquitto_certificates"
ca_certificate = os.path.join(certificates_path, "ca/ca.crt")
client_certificate = os.path.join(certificates_path, "client6/client6.crt")
client_key = os.path.join(certificates_path, "client6/client6.key")
# 192.168.35.113 - IP адрес или hostname Mosquitto сервера
mqtt_server_host = "192.168.35.113"
mqtt_server_port = 8883
mqtt_keepalive = 60

DHT_PIN = 17
# ds18b20_id = "28-3c01d0752a52"
ds18b20_id_room = "28-3c01d075687d"
# ds18b20_id = "28-3c01d07538af"
ds18b20_id_out = "28-3cd5f648d8b7"
# ds18b20_id_room = "28-0115718d9dff"
# ds18b20_id_out = "28-011564b20bff"


dict_relay_pins = {
    "ROOM01_HEATER_PIN": 27,
    "RELAY01_PIN": 12,
    "RELAY02_PIN": 16,
    "RELAY03_PIN": 20,
    "RELAY04_PIN": 21,
}
NTP_SERVER = '0.ru.pool.ntp.org'

PATH = "settings.ini"
