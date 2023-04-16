import Adafruit_BMP.BMP085 as BMP085
import Adafruit_DHT as DHT11
import RPi.GPIO as GPIO
import I2C_LCD_driver
from config import *
import adafruit_ds3231
import board, time, ntplib, smbus2, bme280
from socket import gaierror
from panel_commands import KEY_HUMIDITY, KEY_PRESSURE, KEY_TEMP

class Sensors:
    def __init__(self, name):
        self.name = name

    def get_BMP085_data(self):
        ''' Default constructor will pick a default I2C bus.
            For the Raspberry Pi this means you should hook up to the only exposed I2C bus
            from the main GPIO header and the library will figure out the bus number based
            on the Pi's revision.'''
        sensor = BMP085.BMP085()
        ''' Optionally you can override the bus number:
            sensor = BMP085.BMP085(busnum=2)
            You can also optionally change the BMP085 mode to one of BMP085_ULTRALOWPOWER,
            BMP085_STANDARD, BMP085_HIGHRES, or BMP085_ULTRAHIGHRES.  See the BMP085
            datasheet for more details on the meanings of each mode (accuracy and power
            consumption are primarily the differences).  The default mode is STANDARD.
            sensor = BMP085.BMP085(mode=BMP085.BMP085_ULTRAHIGHRES)'''
        dict_BMP085 = {
            KEY_TEMP: round(sensor.read_temperature(), 2),
            "BMP085_press_pa": round(sensor.read_pressure(), 0),
            KEY_PRESSURE: round((sensor.read_pressure() * 0.00750062), 2),
            "BMP085_alt": round(sensor.read_altitude(), 2),
            "BMP085_sl_press_pa": round(sensor.read_sealevel_pressure(), 0),
            "BMP085_sl_press_hg": round((sensor.read_sealevel_pressure() * 0.00750062), 2),
        }
        return dict_BMP085

    def get_DHT11_data(self, dht_pin): 
        sensor = DHT11.DHT11
        humidity, temp = DHT11.read_retry(sensor, dht_pin)    
        dict_DHT11 = {
            KEY_TEMP: temp,
            KEY_HUMIDITY: humidity,
        }
        return dict_DHT11

    def get_ds18b20_data(self, ds18b20_id):
        f = open('/sys/bus/w1/devices/' + ds18b20_id + '/w1_slave', 'r')
        # Читаем первую строку
        line = f.readline()
        if (line.find('YES') != -1):
            # Читаем вторую строку
            line = f.readline()
            temp = line.rsplit('t=', 1)
            f.close()
            temp = int(temp[1])/float(1000)
        else:
            temp = None
        dict_ds18b20 = {
                KEY_TEMP: temp,
            }
        return dict_ds18b20

    def set_gpio_pin(self, pin, high_low):
        GPIO.output(pin, high_low)

    def init_gpio_pins(self):
        # Disable warnings
        GPIO.setwarnings(False)
        # Cброс состояний портов (все конфигурируются на вход - INPUT)
        GPIO.cleanup()
        # Режим нумерации пинов - по названию (не по порядковому номеру на разъеме)
        GPIO.setmode(GPIO.BCM)
        for pin in dict_relay_pins.values():
            # Пин pin в режим вывода (OUTPUT)
            GPIO.setup(pin, GPIO.OUT)

    def get_rtc_time(self):
        i2c = board.I2C()  # uses board.SCL and board.SDA
        rtc = adafruit_ds3231.DS3231(i2c)
        return time.mktime(rtc.datetime)

    def set_rtc_time(self, time_date_to_set):
        i2c = board.I2C()  # uses board.SCL and board.SDA
        rtc = adafruit_ds3231.DS3231(i2c)
        #                      year, mon, date, hour, min, sec, wday, yday, isdst
        rtc.datetime = time_date_to_set

    def set_rtc_time_ntp(self):
        ntp_client = ntplib.NTPClient()
        try:
            response = ntp_client.request(NTP_SERVER)
        except (ntplib.NTPException, gaierror) as error:
            print(error)
            self.set_rtc_time(time.localtime())
        else:
            self.set_rtc_time(time.localtime(response.tx_time))    

    def get_bme280_data(self, port, address):
        bus = smbus2.SMBus(port)
        calibration_params = bme280.load_calibration_params(bus, address)
        # the sample method will take a single reading and return a
        # compensated_reading object
        data = bme280.sample(bus, address, calibration_params)
        dict_BME285 = {
            KEY_TEMP: round(data.temperature, 2),
            "BMP285_press_hpa": round(data.pressure, 2),
            KEY_PRESSURE: round((data.pressure * 0.750062), 2),
            KEY_HUMIDITY: round(data.humidity, 2),
        }
        bus.close()
        return dict_BME285


if __name__ == "__main__":
    while True:
        sensors = Sensors('ROOM01')
        sensors.init_gpio_pins()
        # print(sensors01.get_BMP085_data())
        # print(sensors.get_DHT11_data(DHT_PIN))
        print(sensors.get_ds18b20_data(ds18b20_id_out))
        print(sensors.get_ds18b20_data(ds18b20_id_room))
        print(f'BME280 temperature: {sensors.get_bme280_data(1, 0x76)[KEY_TEMP]}')
        print(f'BME280 humidity: {sensors.get_bme280_data(1, 0x76)[KEY_HUMIDITY]}')
        print(f'BME280 pressure: {sensors.get_bme280_data(1, 0x76)[KEY_PRESSURE]}')

        time.sleep(10)

        # Cброс состояний портов (все конфигурируются на вход - INPUT)
        # Выключить обогреватель в комнате 01
        # sensors.set_gpio_pin (dict_relay_pins["ROOM01_HEATER_PIN"], GPIO.LOW)
        # Включить обогреватель в комнате 01
        # sensors.set_gpio_pin (dict_relay_pins["ROOM01_HEATER_PIN"], GPIO.HIGH)
        # Включить реле 01
        # sensors.set_gpio_pin (dict_relay_pins["RELAY01_PIN"], GPIO.LOW)
        # Выключить реле 01 
        # sensors.set_gpio_pin (dict_relay_pins["RELAY01_PIN"], GPIO.HIGH)
        # Включить реле 02
        # sensors.set_gpio_pin (dict_relay_pins["RELAY02_PIN"], GPIO.LOW)
        # Выключить реле 02
        # sensors.set_gpio_pin (dict_relay_pins["RELAY02_PIN"], GPIO.HIGH)
        # Включить реле 03
        # sensors.set_gpio_pin (dict_relay_pins["RELAY03_PIN"], GPIO.LOW)
        # Выключить реле 03
        # sensors.set_gpio_pin (dict_relay_pins["RELAY03_PIN"], GPIO.HIGH)
        # Включить реле 04
        # sensors.set_gpio_pin (dict_relay_pins["RELAY04_PIN"], GPIO.LOW)
        # Выключить реле 04
        # sensors.set_gpio_pin (dict_relay_pins["RELAY04_PIN"], GPIO.HIGH)
        # lcd = I2C_LCD_driver.lcd()
        # lcd.lcd_display_string("Temperature:", 1)
        # lcd.lcd_display_string(str(sensors01.get_DHT11_data(DHT_PIN)["DHT11_temp"]), 2)
        # sensors.set_rtc_time_ntp()

    '''while True:
        local_time = time.localtime(sensors.get_rtc_time())
        current_date = time.strftime('%m-%d-%Y %a', local_time)
        current_time = time.strftime('%H:%M:%S', local_time)
        lcd.lcd_display_string(current_date, 1)
        lcd.lcd_display_string(current_time, 2)
        time.sleep(1)'''