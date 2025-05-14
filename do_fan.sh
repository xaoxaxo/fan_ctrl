#! /bin/sh

### BEGIN INIT INFO
# Provides:          fan_ctrl.py
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
### END INIT INFO

# If you want a command to always run, put it here

# Carry out specific functions when asked to by the system
case "$1" in
  start)
    echo "Starting fan_ctrl.py"
    /home/pi/script/fan_ctrl.py &
    ;;
  stop)
    echo "Stopping fan_ctrl.py"
    pkill -f /home/pi/script/fan_ctrl.py
    ;;
  *)
    echo "Usage: /etc/init.d/do_fan.sh {start|stop}"
    exit 1
    ;;
esac

exit 0