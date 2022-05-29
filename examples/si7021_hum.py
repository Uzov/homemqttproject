import smbus
import time

bus = smbus.SMBus(1)

# reset device
bus.write_byte(0x40, 0xfe)
time.sleep(.3)

# read relative humidity (no hold master mode)
bus.write_byte(0x40, 0xF5)
err = True
while err:
	try:
		rh_raw = bus.read_byte(0x40)
		err = False
	except:
		time.sleep(.01)
rh_raw += bus.read_byte(0x40) << 8
print(rh_raw)

# 0xE0 get the temperature measurement from RH measurement instead of measuring again using 0xF3
bus.write_byte(0x40, 0xE0)
t_raw = bus.read_byte(0x40)
t_raw += bus.read_byte(0x40) << 8
print(t_raw)

# compute and save human readable humidity and temp values
RH = 125.0*rh_raw/65536.0 - 6.0
Tc = 175.72*t_raw/65536.0 - 46.85
Tf = Tc * 1.8 + 32

print("tempf {0} tempc {1} humidity {2}".format(Tf, Tc, RH))