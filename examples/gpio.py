#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Подключаем необходимые библиотеки (для задержки по времени и GPIO)
import time
import RPi.GPIO as GPIO

# Установим номера пинов GPIO, с которыми будем работать
LED = 27
KEY = 17

# Делаем сброс состояний портов (все конфигурируются на вход - INPUT)
GPIO.cleanup()
# Режим нумерации пинов - по названию (не по порядковому номеру на разъеме)
GPIO.setmode(GPIO.BCM)
# Сконфигурируем пин LED на вывод (OUTPUT)
GPIO.setup(LED, GPIO.OUT)
# Установим низкий уровень (0) на пине LED
GPIO.output(LED, GPIO.LOW)
# Сконфигурируем пин KEY на ввод (INPUT)
GPIO.setup(KEY, GPIO.IN)
# Выведем на экран текст-приветствие
print ('Hello! Blink...blink...')

# Проверка на прерывание программы с клавиатуры (CTRL+C)
try:
    # Вечный цикл
    while True:
        # Если кнопка нажата (на пине KEY низкий уровень 0V)
        if GPIO.input(KEY) == False:
            # Устанавливаем задержку 0,1 сек. и выводим сообщение
            timeout = 0.1
            print ('Key pressed.')
        else:
            # в противном случае задержка - 0,5 сек.
            timeout = 0.5
        # Засветим светодиод, подключенный к пину LED
        GPIO.output(LED, GPIO.HIGH)
        # Подождем (выполним заданную выше задержку)
        time.sleep(timeout)
        # Погасим светодиод, подключенный к пину LED
        GPIO.output(LED, GPIO.LOW)
        time.sleep(timeout)
# Если комбинация клавиш CTRL+C была нажата - сброс пинов и завершение
except KeyboardInterrupt:
    GPIO.cleanup()