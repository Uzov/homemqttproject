from audioop import add
from concurrent.futures import thread
from ctypes import addressof
from email import message
import threading
from config import *
from panel_commands import *
from panel_sensors import *
import paho.mqtt.client as mqtt
import time
import json
import settings as conf_file
from threading import Thread, main_thread
from distutils.util import strtobool


class Panel:
    
    def __init__(self, name, sensors):
        self.name = name
        self.sensors = sensors
        self.is_heater_on = False
        self.auto = False
        self.port = 1
        self.address = 0x76

    def print_action_with_name_prefix(self, action):
        log_time = time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(sensors.get_rtc_time()))
        print("{}: {}, {}".format(log_time, self.name, action))
   
    def get_room01_temp(self):
        self.print_action_with_name_prefix("Getting room01 temperature.")
        # return sensors.get_DHT11_data(DHT_PIN)[KEY_TEMP]
        return sensors.get_bme280_data(self.port, self.address)[KEY_TEMP]

    def get_room01_humidity(self):
        self.print_action_with_name_prefix("Getting room01 humidity.")
        # return sensors.get_DHT11_data(DHT_PIN)[KEY_HUMIDITY]
        return sensors.get_bme280_data(self.port, self.address)[KEY_HUMIDITY]

    def get_room01_pressure(self):
        self.print_action_with_name_prefix("Getting room01 pressure.")
        # return sensors.get_BMP085_data()[KEY_PRESSURE]
        return sensors.get_bme280_data(self.port, self.address)[KEY_PRESSURE]
   
    def get_outer_temp(self):
        self.print_action_with_name_prefix("Getting outer temperature.")
        return sensors.get_ds18b20_data(ds18b20_id_out)[KEY_TEMP]
    
    def get_heater_state(self):
        self.print_action_with_name_prefix("Getting heater state")
        return self.is_heater_on

    def turn_on_room01_heater(self):
        self.print_action_with_name_prefix("Turning on room01 heater.")
        sensors.set_gpio_pin(dict_relay_pins["ROOM01_HEATER_PIN"], GPIO.HIGH)
        self.is_heater_on = True
        conf_file.update_setting(PATH, 'Settings', 'heater_on', 'True')

    def turn_off_room01_heater(self):
        self.print_action_with_name_prefix("Turning off room01 heater.")
        sensors.set_gpio_pin(dict_relay_pins["ROOM01_HEATER_PIN"], GPIO.LOW)
        self.is_heater_on = False
        conf_file.update_setting(PATH, 'Settings', 'heater_on', 'False')

    def turn_on_relay01(self):
        self.print_action_with_name_prefix("Turning on relay01.")
        sensors.set_gpio_pin(dict_relay_pins["RELAY01_PIN"], GPIO.LOW)
        self.is_relay01_on = True
        conf_file.update_setting(PATH, 'Settings', 'relay01_on', 'True')

    def turn_off_relay01(self):
        self.print_action_with_name_prefix("Turning off relay01.")
        sensors.set_gpio_pin(dict_relay_pins["RELAY01_PIN"], GPIO.HIGH)
        self.is_relay01_on = False
        conf_file.update_setting(PATH, 'Settings', 'relay01_on', 'False')

    def turn_on_relay02(self):
        self.print_action_with_name_prefix("Turning on relay02.")
        sensors.set_gpio_pin(dict_relay_pins["RELAY02_PIN"], GPIO.LOW)
        self.is_relay02_on = True
        conf_file.update_setting(PATH, 'Settings', 'relay02_on', 'True')

    def turn_off_relay02(self):
        self.print_action_with_name_prefix("Turning off relay02.")
        sensors.set_gpio_pin(dict_relay_pins["RELAY02_PIN"], GPIO.HIGH)
        self.is_relay02_on = False
        conf_file.update_setting(PATH, 'Settings', 'relay02_on', 'False')

    def turn_on_relay03(self):
        self.print_action_with_name_prefix("Turning on relay03.")
        sensors.set_gpio_pin(dict_relay_pins["RELAY03_PIN"], GPIO.LOW)
        self.is_relay03_on = True
        conf_file.update_setting(PATH, 'Settings', 'relay03_on', 'True')

    def turn_off_relay03(self):
        self.print_action_with_name_prefix("Turning off relay03.")
        sensors.set_gpio_pin(dict_relay_pins["RELAY03_PIN"], GPIO.HIGH)
        self.is_relay03_on = False
        conf_file.update_setting(PATH, 'Settings', 'relay03_on', 'False')

    def turn_on_relay04(self):
        self.print_action_with_name_prefix("Turning on relay04.")
        sensors.set_gpio_pin(dict_relay_pins["RELAY04_PIN"], GPIO.LOW)
        self.is_relay04_on = True
        conf_file.update_setting(PATH, 'Settings', 'relay04_on', 'True')
    
    def turn_off_relay04(self):
        self.print_action_with_name_prefix("Turning off relay04.")
        sensors.set_gpio_pin(dict_relay_pins["RELAY04_PIN"], GPIO.HIGH)
        self.is_relay04_on = False
        conf_file.update_setting(PATH, 'Settings', 'relay04_on', 'False')
    
    def set_auto_true(self):
        self.print_action_with_name_prefix("Auto_mode_true")
        self.auto = True
        conf_file.update_setting(PATH, 'Settings', 'auto_on', 'True')

    def set_auto_false(self):
        self.print_action_with_name_prefix("Auto_mode_false")
        self.auto = False
        conf_file.update_setting(PATH, 'Settings', 'auto_on', 'False')
    
    def set_max_room01_temp(self, temp):
        self.max_temp_degree = temp
        self.print_action_with_name_prefix("Setting maximum temperature to {} degree".format(temp))
        conf_file.update_setting(PATH, 'Settings', 'max_room01_temp', str(temp))
    
class PanelCommandProcessor:
    commands_topic = ""
    processed_commands_topic = ""
    synch_topic = ""
    active_instance = None
    max_temp_degree = int(conf_file.get_setting(PATH, 'Settings', 'max_room01_temp'))
    delta = 0

    def __init__(self, name, panel):
        self.name = name
        self.panel = panel
        PanelCommandProcessor.commands_topic = \
            "alvidino/{}/commands".format(self.name)
        PanelCommandProcessor.processed_commands_topic = \
            "alvidino/{}/executedcommands".format(self.name)
        PanelCommandProcessor.answers_topic = \
            "alvidino/{}/answers".format(self.name)
        PanelCommandProcessor.synch_topic = \
            "alvidino/{}/synch".format(self.name)
        self.client = mqtt.Client(protocol=mqtt.MQTTv311)
        PanelCommandProcessor.active_instance = self
        self.client.on_connect = PanelCommandProcessor.on_connect
        self.client.on_message = PanelCommandProcessor.on_message
        self.client.on_subscribe = PanelCommandProcessor.on_subscribe
        self.client.tls_set(ca_certs=ca_certificate,
            certfile=client_certificate,
            keyfile=client_key)
        self.client.username_pw_set(username="mqttuser", password="password")
        self.client.connect(host=mqtt_server_host,
                            port=mqtt_server_port,
                            keepalive=mqtt_keepalive)        

    # Начальная синхронизация дашборда
    def synch_dashboard(self):
        
        temp = int(conf_file.get_setting(PATH, 'Settings', 'max_room01_temp'))
        panel.set_max_room01_temp(temp)
        self.publish_synch_message(CMD_SET_MAX_ROOM01_TEMP, temp)
        
        cond_auto = strtobool(conf_file.get_setting(PATH, 'Settings', 'auto_on'))
        if (cond_auto):
            panel.set_auto_true()
            self.publish_synch_message(CMD_SET_AUTO_TRUE, None)
        else:
            panel.set_auto_false()
            self.publish_synch_message(CMD_SET_AUTO_FALSE, None)
        
        # Если автоматическое управление нагревателем включено, то ручное включение нагревателя игнорируется!
        # if (strtobool(conf_file.get_setting(PATH, 'Settings', 'heater_on')) and not cond_auto):
        if (strtobool(conf_file.get_setting(PATH, 'Settings', 'heater_on'))):
            panel.turn_on_room01_heater()
            self.publish_synch_message(CMD_TURN_ON_ROOM01_HEATER, None)
        else:
            panel.turn_off_room01_heater()
            self.publish_synch_message(CMD_TURN_OFF_ROOM01_HEATER, None)
        
        if (strtobool(conf_file.get_setting(PATH, 'Settings', 'relay01_on'))):
            panel.turn_on_relay01()
            self.publish_synch_message(CMD_TURN_ON_RELAY01, None)
        else:
            panel.turn_off_relay01()
            self.publish_synch_message(CMD_TURN_OFF_RELAY01, None)

        if (strtobool(conf_file.get_setting(PATH, 'Settings', 'relay02_on'))):
            panel.turn_on_relay02()
            self.publish_synch_message(CMD_TURN_ON_RELAY02, None)
        else:
            panel.turn_off_relay02()
            self.publish_synch_message(CMD_TURN_OFF_RELAY02, None)
        
        if (strtobool(conf_file.get_setting(PATH, 'Settings', 'relay03_on'))):
            panel.turn_on_relay03()
            self.publish_synch_message(CMD_TURN_ON_RELAY03, None)
        else:
            panel.turn_off_relay03()
            self.publish_synch_message(CMD_TURN_OFF_RELAY03, None)
        
        if (strtobool(conf_file.get_setting(PATH, 'Settings', 'relay04_on'))):
            panel.turn_on_relay04()
            self.publish_synch_message(CMD_TURN_ON_RELAY04, None)
        else:
            panel.turn_off_relay04()
            self.publish_synch_message(CMD_TURN_OFF_RELAY04, None)
        
    @staticmethod
    def on_connect(client, userdata, flags, rc):
        log_time = time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(sensors.get_rtc_time()))
        print("{}, Result from connect: {}".format(log_time, mqtt.connack_string(rc)))
        # Check whether the result form connect is the CONNACK_ACCEPTED connack code
        if rc == mqtt.CONNACK_ACCEPTED:
            # Subscribe to the commands topic filter
            client.subscribe(PanelCommandProcessor.commands_topic, qos=2)

    @staticmethod
    def on_subscribe(client, userdata, mid, granted_qos):
        log_time = time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(sensors.get_rtc_time()))
        print("{}, I've subscribed with QoS: {}".format(log_time, granted_qos[0]))
        PanelCommandProcessor.active_instance.synch_dashboard()

    @staticmethod
    def on_message(client, userdata, msg):
        if msg.topic == PanelCommandProcessor.commands_topic:
            log_time = time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(sensors.get_rtc_time()))
            print("{0}, Received message payload: {1}".format(log_time, str(msg.payload)))
            try:
                message_dictionary = json.loads(msg.payload)
                if COMMAND_KEY in message_dictionary:
                    command = message_dictionary[COMMAND_KEY]
                    panel = PanelCommandProcessor.active_instance.panel
                    is_command_executed = False
                    # BOF new code
                    if command == CMD_SET_MAX_ROOM01_TEMP:
                        PanelCommandProcessor.max_temp_degree = message_dictionary[KEY_TEMP]
                    command_methods_dictionary = {
                        CMD_GET_ROOM01_TEMP: lambda: panel.get_room01_temp(),
                        CMD_GET_ROOM01_HUMIDITY: lambda: panel.get_room01_humidity(),
                        CMD_GET_ROOM01_PRESSURE: lambda: panel.get_room01_pressure(),
                        CMD_GET_OUTER_TEMP: lambda: panel.get_outer_temp(),
                        CMD_GET_HEATER_STATE: lambda: panel.get_heater_state(),
                        CMD_TURN_ON_ROOM01_HEATER: lambda: panel.turn_on_room01_heater(),
                        CMD_TURN_OFF_ROOM01_HEATER: lambda: panel.turn_off_room01_heater(),
                        CMD_TURN_ON_RELAY01: lambda: panel.turn_on_relay01(),
                        CMD_TURN_OFF_RELAY01: lambda: panel.turn_off_relay01(),
                        CMD_TURN_ON_RELAY02: lambda: panel.turn_on_relay02(),
                        CMD_TURN_OFF_RELAY02: lambda: panel.turn_off_relay02(),
                        CMD_TURN_ON_RELAY03: lambda: panel.turn_on_relay03(),
                        CMD_TURN_OFF_RELAY03: lambda: panel.turn_off_relay03(),
                        CMD_TURN_ON_RELAY04: lambda: panel.turn_on_relay04(),
                        CMD_TURN_OFF_RELAY04: lambda: panel.turn_off_relay04(),
                        CMD_SET_AUTO_TRUE: lambda: panel.set_auto_true(),
                        CMD_SET_AUTO_FALSE: lambda: panel.set_auto_false(),
                        CMD_SET_MAX_ROOM01_TEMP: lambda: panel.set_max_room01_temp(PanelCommandProcessor.max_temp_degree),
                    }
                    if command in command_methods_dictionary:
                        method = command_methods_dictionary[command]
                        # Call the method
                        returned_value = method()
                        is_command_executed = True
                    if is_command_executed:
                        PanelCommandProcessor.active_instance.publish_processed_message(
                            message_dictionary)
                        if returned_value is not None:
                            PanelCommandProcessor.active_instance.publish_answer_message(
                                message_dictionary, returned_value)
                    else:
                        log_time = time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(sensors.get_rtc_time()))
                        print("{}, I've received a message with an unsupported command.".format(log_time))
            except ValueError:
                # msg is not a dictionary
                # No JSON object could be decoded
                log_time = time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(sensors.get_rtc_time()))
                print("{}, I've received an invalid message.".format(log_time))

    def publish_processed_message(self, message):
        response_message = json.dumps({
            SUCCESFULLY_PROCESSED_COMMAND_KEY:
                message[COMMAND_KEY]})
        result = self.client.publish(
            topic=self.__class__.processed_commands_topic,
            payload=response_message)
        log_time = time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(sensors.get_rtc_time()))
        print("{}, The message {} is successfully executed.".format(log_time, response_message))
        return result
    
    def publish_answer_message(self, message, value):
        response_message = json.dumps({
        ANSWER_KEY: message[COMMAND_KEY],
        ANSW_DATA: value,})
        result = self.client.publish(
            topic=self.__class__.answers_topic,
            payload=response_message)
        log_time = time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(sensors.get_rtc_time()))
        print("{}, The answer message {} is successfully sent.".format(log_time, response_message))
        return result

    def publish_synch_message(self, message, value):
        if (value is not None):
            response_message = json.dumps({
            SYNCH_KEY: message,
            SYNCH_DATA: value,})
        else:
            response_message = json.dumps({
            SYNCH_KEY: message,})
        result = self.client.publish(
            topic=self.__class__.synch_topic,
            payload=response_message)
        log_time = time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(sensors.get_rtc_time()))
        print("{}, The answer message {} is successfully sent.".format(log_time, response_message))
        return result

    def process_incoming_commands(self):
        self.client.loop()
    
 # Функция отображает информацию на LCD дисплее:
def show_lcd_info(start_time):
    lock=threading.Lock()
    lcd = I2C_LCD_driver.lcd()
    lcd.lcd_clear()
    # Счётчик, чтобы часто не опрашивать датчики, иначе он выдаёт None
    r = 3
    while True:
        local_time = time.localtime(sensors.get_rtc_time())
        if (r >= 3):
            with lock:
                # room_climate = sensors.get_DHT11_data(DHT_PIN)
                # pressure = sensors.get_BMP085_data()
                room_climate = sensors.get_bme280_data(panel.port, panel.address)
                out_climate = sensors.get_ds18b20_data(ds18b20_id_out)
            r = 0
        if (0 < (time.time() - start_time) < 5):
            lcd.lcd_display_string(time.strftime(' %d-%m-%Y %a ', local_time), 1, 0)
            lcd.lcd_display_string(time.strftime(' -= %H:%M:%S =- ', local_time), 2, 0)
            # lcd.lcd_display_string(f't={round(room_climate[KEY_TEMP], 1)}C   ', 2, 9)
        if (5 < (time.time() - start_time) < 10):
            lcd.lcd_display_string(f'Room temp.:{round(room_climate[KEY_TEMP], 2)}C   ', 1, 0)
            lcd.lcd_display_string(f'Room hum.:{round(room_climate[KEY_HUMIDITY], 2)}% ', 2, 0)
        if (10 < (time.time() - start_time) < 15):
            lcd.lcd_display_string(f'Out temp.:{round(out_climate[KEY_TEMP], 2)}C   ', 1, 0)
            # lcd.lcd_display_string(f'Room hum.:{room_climate[KEY_HUMIDITY]}% ', 2, 0)
            lcd.lcd_display_string(f'Pressure:{round(room_climate[KEY_PRESSURE], 2)}mm  ', 2, 0)
        if (time.time() - start_time) > 15:
            # Очистка дисплея. Но лучше не очищать, а перезаписывать.
            # lcd.lcd_clear()
            start_time = time.time()
            r = r + 1
            time.sleep(1)

def main_func():
    lock=threading.Lock()
    while True:
        # Process messages and the commands every 1 second
        with lock:
            panel_command_processor.process_incoming_commands()
            # room_temp = sensors.get_DHT11_data(DHT_PIN)[KEY_TEMP]
            # room_temp = sensors.get_ds18b20_data(ds18b20_id_room)[KEY_TEMP]
            room_temp = sensors.get_bme280_data(panel.port, panel.address)[KEY_TEMP]

        if ((room_temp is not None) and panel.auto): 
            room_temp=int(room_temp)
            if (room_temp < (panel_command_processor.max_temp_degree - panel_command_processor.delta)) \
                and (not panel.is_heater_on):
                panel.turn_on_room01_heater()
                panel_command_processor.publish_processed_message({COMMAND_KEY:CMD_TURN_ON_ROOM01_HEATER,})
                panel_command_processor.publish_synch_message (CMD_TURN_ON_ROOM01_HEATER, None)
            if (room_temp > (panel_command_processor.max_temp_degree)) \
                and (panel.is_heater_on):
                panel.turn_off_room01_heater()
                panel_command_processor.publish_processed_message({COMMAND_KEY:CMD_TURN_OFF_ROOM01_HEATER,})
                panel_command_processor.publish_synch_message (CMD_TURN_OFF_ROOM01_HEATER, None)
        time.sleep(1)
 
if __name__ == "__main__":
    sensors = Sensors('ROOM01')
    sensors.init_gpio_pins()
    sensors.set_rtc_time_ntp()
    panel = Panel('ROOM01', sensors)
    panel_command_processor = PanelCommandProcessor('ROOM01', panel)
    timestamp = time.time()
    
    # Основной 
    main_trd = Thread(target=main_func, args=())
    main_trd.daemon=False
    main_trd.start()

    # Отображение информации на LCD дисплее, запускаем как отдельный процесс!
    lcd_show = Thread(target=show_lcd_info, args=(timestamp,))
    lcd_show.daemon=True
    lcd_show.start()
    
    