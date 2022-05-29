import adafruit_ds3231
import time
import board

i2c = board.I2C()  # uses board.SCL and board.SDA
rtc = adafruit_ds3231.DS3231(i2c)
#                      year, mon, date, hour, min, sec, wday, yday, isdst
# rtc.datetime = time.struct_time((2022,2,21,0,34,0,1,-1,-1))
t = rtc.datetime
print(t)
print(t.tm_mday,'-',t.tm_mon,'-',t.tm_year,' ',t.tm_hour,':',t.tm_min,':',t.tm_sec)
print(t.tm_zone)