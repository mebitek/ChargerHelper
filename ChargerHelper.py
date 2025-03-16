#!/usr/bin/env python

import logging
import sys
import os

import dbus
import _thread as thread

from charger_config import ChargerConfig

sys.path.insert(1, "/data/SetupHelper/velib_python")
from vedbus import VeDbusService, VeDbusItemImport, VeDbusItemExport

from gi.repository import GLib



class ChargerHelperService:

    def __init__(self, servicename, deviceinstance, paths, productname='IP22 VeBus Helper', connection='DBUS',
                 config=None):
        self.config = config or ChargerConfig()
        self._dbusservice = VeDbusService(servicename, register=False)
        self._paths = paths

        # Create the management objects, as specified in the ccgx dbus-api document
        self._dbusservice.add_path('/Mgmt/ProcessName', __file__)
        self._dbusservice.add_path('/Mgmt/ProcessVersion', config.get_version())
        self._dbusservice.add_path('/Mgmt/Connection', connection)

        # Create the mandatory objects
        self._dbusservice.add_path('/DeviceInstance', deviceinstance)
        # value used in ac_sensor_bridge.cpp of dbus-cgwacs
        self._dbusservice.add_path('/ProductId', 41772)
        self._dbusservice.add_path('/ProductName', productname)
        self._dbusservice.add_path('/DeviceName', productname)
        self._dbusservice.add_path('/FirmwareVersion', 0x0136)
        self._dbusservice.add_path('/HardwareVersion', 8)
        self._dbusservice.add_path('/Connected', 1)
        self._dbusservice.add_path('/Serial', "xxxxx")

        for path, settings in self._paths.items():
            self._dbusservice.add_path(
                path, settings['initial'], writeable=True, onchangecallback=self._handlechangedvalue)

        self._dbusservice.register()
        GLib.timeout_add(1000, self._update)

    def _update(self):

        dbus_conn = dbus.SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus()
        ac_input_1 = VeDbusItemImport(dbus_conn, 'com.victronenergy.settings', '/Settings/SystemSetup/AcInput1')

        device = self.config.get_device()
        has_charger = device in dbus_conn.list_names()

        if has_charger:

            serial = VeDbusItemImport(dbus_conn, device, '/Serial')
            self._dbusservice['/Serial'] = serial.get_value()

            self._dbusservice['/Ac/ActiveIn/Connected'] = 1

            ac_input_1.set_value(1)
            current = VeDbusItemImport(dbus_conn, device, '/Dc/0/Current')
            voltage = VeDbusItemImport(dbus_conn, device, '/Dc/0/Voltage')
            state = VeDbusItemImport(dbus_conn, device, '/State')
            temperature = VeDbusItemImport(dbus_conn, device, '/Dc/0/Temperature')

            logging.debug("/State: %s", state.get_value())
            logging.debug("CURRENT %s" % current.get_value())

            if current is not None and current.get_value() is not None:
                grid_voltage = float(self.config.get_voltage())
                power = current.get_value() * voltage.get_value()
                self._dbusservice[ '/Ac/ActiveIn/ActiveInput'] = 0

                self._dbusservice['/Ac/ActiveIn/P'] = power
                self._dbusservice['/Ac/ActiveIn/L1/P'] = power
                self._dbusservice['/Ac/ActiveIn/L1/I'] = power / grid_voltage
                self._dbusservice['/Ac/ActiveIn/L1/V'] = grid_voltage
                self._dbusservice['/State'] = state.get_value()
                self._dbusservice['/Dc/0/Voltage'] = voltage.get_value()
                self._dbusservice['/Dc/0/Current'] = -current.get_value()
                self._dbusservice['/Dc/0/Power'] = current.get_value() * voltage.get_value()
                self._dbusservice['/Dc/0/Temperature'] = temperature.get_value()
            else:
                self.set_disconnected()
                ac_input_1.set_value(0)
        else:
                self.set_disconnected()
                ac_input_1.set_value(0)

        index = self._dbusservice['/UpdateIndex'] + 1  # increment index
        if index > 255:  # maximum value of the index
            index = 0  # overflow from 255 to 0
        self._dbusservice['/UpdateIndex'] = index
        return True

    def _handlechangedvalue(self, value):
        return True

    def set_disconnected(self):
        self._dbusservice['/Ac/ActiveIn/Connected'] = 0
        self._dbusservice['/State'] = 0
        self._dbusservice['/Dc/0/Voltage'] = None
        self._dbusservice['/Dc/0/Current'] = None
        self._dbusservice[ '/Ac/ActiveIn/ActiveInput'] = 240

        self._dbusservice['/Ac/ActiveIn/P'] = None
        self._dbusservice['/Ac/ActiveIn/L1/P'] = None
        self._dbusservice['/Ac/ActiveIn/L1/I'] = None
        self._dbusservice['/Ac/ActiveIn/L1/V'] = None

def main():
    config = ChargerConfig()

    # set logging level to include info level entries
    level = logging.INFO
    if config.get_debug():
        level = logging.DEBUG
    logging.basicConfig(level=level)
    logging.info(">>>>>>>>>>>>>>>> Tasmota Inverter Starting <<<<<<<<<<<<<<<<")

    thread.daemon = True  # allow the program to quit
    from dbus.mainloop.glib import DBusGMainLoop

    DBusGMainLoop(set_as_default=True)

    charger_service = ChargerHelperService(
        servicename='com.victronenergy.vebus.charger_helper',
        deviceinstance=51,
        paths={
            '/Ac/ActiveIn/Connected': {'initial': 1},
            '/Ac/PowerMeasurementType': {'initial': 4},
            '/Ac/NumberOfAcInputs': {'initial': 1},
            '/Ac/NumberOfPhases': {'initial': 1},
            '/Ac/ActiveIn/ActiveInput': {'initial': 0},

            '/Ac/ActiveIn/CurrentLimit': {'initial': 15},
            '/Ac/In/0/CurrentLimit': {'initial': 15},
            '/Dc/0/Voltage': {'initial': 0},
            '/Dc/0/Current': {'initial': 0},
            '/Dc/0/Power': {'initial': 0},
            '/Dc/0/Temperature': {'initial': 0},

            '/Ac/ActiveIn/L1/F': {'initial': 50},
            '/Ac/ActiveIn/L1/I': {'initial': 0},
            '/Ac/ActiveIn/L1/P': {'initial': 0},
            '/Ac/ActiveIn/L1/V': {'initial': 0},
            '/Ac/ActiveIn/P': {'initial': 0},
            '/Ac/ActiveIn/S': {'initial': 0},

            '/Mode': {'initial': 1},
            '/State': {'initial': 0},


            '/UpdateIndex': {'initial': 0}
        },
        config=config
    )

    logging.info('Connected to dbus, and switching over to GLib.MainLoop() (= event based)')
    mainloop = GLib.MainLoop()
    mainloop.run()

if __name__ == "__main__":
    main()