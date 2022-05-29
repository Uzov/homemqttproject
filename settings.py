import configparser
import os
 
# Создание файла конфигурации 
def create_config(path):
    config = configparser.ConfigParser()
    config.add_section("Settings")
    config.set("Settings", "auto_on", "True")
    config.set("Settings", "max_room01_temp", "23")
    config.set("Settings", "heater_on", "False")
    config.set("Settings", "relay01_on", "False")
    config.set("Settings", "relay02_on", "False")
    config.set("Settings", "relay03_on", "False")
    config.set("Settings", "relay04_on", "False")
    with open(path, "w") as config_file:
        config.write(config_file)

# Возвращает объект конфигурации 
def get_config(path):
    if not os.path.exists(path):
        create_config(path)
    config = configparser.ConfigParser()
    config.read(path)
    return config
 
# Получить данные конфигурации
def get_setting(path, section, setting):
    config = get_config(path)
    value = config.get(section, setting)
    '''msg = "{section} {setting} is {value}".format(
        section=section, setting=setting, value=value
    )
    print(msg)'''
    return value

# Обновить данные 
def update_setting(path, section, setting, value):
    config = get_config(path)
    config.set(section, setting, value)
    with open(path, "w") as config_file:
        config.write(config_file)
 
# Удалить данные 
def delete_setting(path, section, setting):
    config = get_config(path)
    config.remove_option(section, setting)
    with open(path, "w") as config_file:
        config.write(config_file)
 
 
if __name__ == "__main__":
    path = "settings.ini"
    auto = get_setting(path, 'Settings', 'auto_on')
    max_room01_temp = get_setting(path, 'Settings', 'max_room01_temp')
    print(auto)
    print(max_room01_temp)
    update_setting(path, "Settings", "max_room01_temp", "25")
    update_setting(path, "Settings", "auto_on", "False")
    # delete_setting(path, "Settings", "auto")
    auto = get_setting(path, 'Settings', 'auto_on')
    max_room01_temp = get_setting(path, 'Settings', 'max_room01_temp')
    print(auto)
    print(max_room01_temp)