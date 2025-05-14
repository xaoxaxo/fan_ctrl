# fan_ctrl

## Description
This program is derived from fan_ctrl.py, which was copied from
https://www.instructables.com/PWM-Regulated-Fan-Based-on-CPU-Temperature-for-Ras/

Thank you for the hard work, Aerandir14

This program is free software: you can redistribute it and/or modify it how you like.
The source did not specify the license, therefore I am not specifying it either.

This is a script - fan speed based on CPU temperature. It will control its speed like it's done on mainstream PC, using Python.

I have reworked the script to suite my needs:
- specify initial fan PWM
- code put into nice class
- changed logic for processor temp measurement.
- added boost for low speeds
- added minimum speed 

### Dependencies

* Tested with Python 2.7 and 3.12
* pip install RPi.GPIO

### Installing

* You can either run as stand-alone script or install it to be run during start-up as a system service

### Executing program - standalone
```
python /home/pi/script/fan_ctrl.py
```
or
```
python /home/pi/script/fan_ctrl.py -TEST
```

### Executing program - service

1. Copy the fan_ctrl.py into /home/pi/script/
2. Copy the do_fan.sh into /etc/init.d
3. To tell systemd to start service now, do this:
```
sudo systemctl start do_fan
```

To tell systemd to start services automatically at boot, you must enable them (once)
```
sudo systemctl enable do_fan
```

