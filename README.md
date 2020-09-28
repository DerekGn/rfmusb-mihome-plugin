# rfmusb-mihome-plugin
A domoticz plugin for energenie mihome OOK devices controlled via a RfmUsb device.

* Supports MIHO07, MIHO021, MIHO022, MIHO023 double sockets
* Supports MIHO008, MIHO024, MIHO025, MIHO026, MIHO071, MIHO072, MIHO073 light switches
* Can pair switch when switch or socket placed in pairing mode

## Installing Plugin

Follow the instructions [here](https://www.domoticz.com/wiki/Using_Python_plugins) for installing the plugin.

## Configuration Settings

The following are the configuration settings for the plugin:

* Serial port is the name of the serial port that the Rfm69 is enumerated.
* Home Addresses is a list of addresses split by a semi colon ;. Defaults to 6c6c6
* Tx Power Level is the Tx power level. Defaults to -2 dbm
* Tx Count is the number of times the switching message is transmitted.Defaults to 5

Each Home Address value allows the use of up to four sockets/switches plus the ability to switch all sockets/switches on or off simultaneously.

Note dependant on the distance the receiving socket the Tx Count and Tx Power Level may need adjustment. It is advised to increase the TX Power Level incrementally until a switch/socket switches on and off reliably.

## Paring A Switch Or Socket

To pair a socket or switch press the switch button for approximately 5 seconds until the LED indicator lamp begins to flash.

From the switch tab turn on the virtual switch that you want to pair the physical switch with.

The LED indicator will switch quickly to indicate that pairing has completed and the switch/socket will switch to on indicated by a solid LED indication light.
