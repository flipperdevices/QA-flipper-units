#!/usr/bin/env python3

import sys, os
import serial
import re

LEAK_THRESHOLD = 3000  # added until units are fixed

def flp_serial_by_name(flp_name):
    if sys.platform == 'darwin':    #MacOS
        flp_serial = '/dev/cu.usbmodemflip_' + flp_name + '1'
    elif sys.platform == 'linux':   #Linux
        flp_serial = '/dev/serial/by-id/usb-Flipper_Devices_Inc._Flipper_' + flp_name + '_flip_' + flp_name + '-if00'

    if os.path.exists(flp_serial):
        return flp_serial
    else:
        if os.path.exists(flp_name):
            return flp_name
        else:
            return ''


def main():
    flp_serial = flp_serial_by_name(sys.argv[1])

    if flp_serial == '':
        print("Name or serial port is invalid")
        sys.exit(1)

    with serial.Serial(flp_serial, timeout=1) as flipper:
        flipper.baudrate = 230400
        flipper.flushOutput()
        flipper.flushInput()

        flipper.timeout = 300

        flipper.read_until(b'>: ').decode("utf-8")
        flipper.write(b"unit_tests\r")
        data = flipper.read_until(b'>: ').decode("utf-8")

        lines = data.split("\r\n")

        tests_re = r"Failed tests: \d{0,}"
        time_re = r"Consumed: \d{0,}"
        leak_re = r"Leaked: \d{0,}"
        status_re = r"Status: \w{3,}"

        tests_pattern = re.compile(tests_re)
        time_pattern = re.compile(time_re)
        leak_pattern = re.compile(leak_re)
        status_pattern = re.compile(status_re)

        tests, time, leak, status = None, None, None, None

        for line in lines:
            print(line)
            if not tests:
                tests = re.match(tests_pattern, line)
            if not time:
                time = re.match(time_pattern, line)
            if not leak:
                leak = re.match(leak_pattern, line)
            if not status:
                status = re.match(status_pattern, line)

        if leak is None or time is None or leak is None or status is None:
            print("Failed to get data. Or output is corrupt")
            sys.exit(1)

        leak = int(re.findall(r"\d+", leak.group(0))[0])
        status = re.findall(r"\w+", status.group(0))[1]
        tests = int(re.findall(r"\d+", tests.group(0))[0])
        time = int(re.findall(r"\d+", time.group(0))[0])

        if tests > 0 or leak > LEAK_THRESHOLD or status != "Passed":
            print(f"Got {tests} failed tests.")
            print(f"Leaked {leak} bytes.")
            print(f"Status by flipper: {status}")
            print(f"Time elapsed {time/1000} seconds.")
            sys.exit(1)

        print(f"Tests ran successfully! Time elapsed {time/1000} seconds. Passed {tests} tests.")
        sys.exit(0)


if __name__ == '__main__':
    main()
