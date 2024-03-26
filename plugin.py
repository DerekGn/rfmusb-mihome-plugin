# Python plugin for controlling energenie OOK devices
#
# Author: DerekGn
#
"""
<plugin key="RfmEnergOok" name="RfmUsb Energenie OOK" author="DerekGn" version="1.0.4" wikilink="http://www.domoticz.com/wiki/plugins/plugin.html" externallink="https://github.com/DerekGn/rfmusb-mihome-ook-plugin">
    <description>
        <h2>RfmUsb Energenie Ook Devices Plugin Version: 1.0.4</h2>
        <br/>
        The RfmUsb Energenie Ook Devices Plugin allows controlling various Energenie OOK devices.
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Supports MIHO07, MIHO021, MIHO022, MIHO023 double sockets</li>
            <li>Supports MIHO008, MIHO024, MIHO025, MIHO026, MIHO071, MIHO072, MIHO073 light switches</li>
            <li>Can pair switch when switch or socket placed in pairing mode</li>
        </ul>
        <h3>Devices</h3>
        <ul style="list-style-type:square">
            <li>Switch - On off control</li>
        </ul>
        <h3>Configuration</h3>
        <ul style="list-style-type:square">
            <li>Serial port is the name of the serial port that the Rfm69 is enumerated</li>
            <li>Home Addresses is a list of addresses split by a semi colon ;. Defaults to 6c6c6</li>
            <li>Tx Power Level is the Tx power level. Defaults to -2 dbm</li>
            <li>Tx Count is the number of times the switching message is transmitted.Defaults to 5</li>
        </ul>
    </description>
    <params>
        <param field="SerialPort" label="Serial Port" width="150px" required="true" default="/dev/serial1"/>
        <param field="Mode1" label="Home Addresses" width="300px" required="true" default="6C6C6"/>
        <param field="Mode3" label="Tx Interval" width="100px" required="true" default="100"/>
        <param field="Mode4" label="Tx Power Level" width="100px" required="true" default="0">
            <options>
                <option label="-2 dbm" value="-2"/>
                <option label="-1 dbm" value="-1"/>
                <option label="0 dbm" value="0"/>
                <option label="1 dbm" value="1"/>
                <option label="2 dbm" value="2"/>
                <option label="3 dbm" value="3"/>
                <option label="4 dbm" value="4"/>
                <option label="5 dbm" value="5"/>
                <option label="6 dbm" value="6"/>
                <option label="7 dbm" value="7"/>
                <option label="8 dbm" value="8"/>
                <option label="9 dbm" value="9"/>
                <option label="10 dbm" value="10"/>
                <option label="11 dbm" value="11"/>
                <option label="12 dbm" value="12"/>
                <option label="13 dbm" value="13"/>
                <option label="14 dbm" value="14"/>
                <option label="15 dbm" value="15"/>
                <option label="16 dbm" value="16"/>
                <option label="17 dbm" value="17"/>
                <option label="18 dbm" value="18"/>
                <option label="19 dbm" value="19"/>
                <option label="20 dbm" value="20"/>
            </options>
        </param>
        <param field="Mode5" label="Tx Count" width="100px" default="5">
            <options>
                <option label="Two" value="2"/>
                <option label="Three" value="3"/>
                <option label="Four" value="4"/>
                <option label="Five" value="5"/>
                <option label="Eight" value="8"/>
                <option label="Thirteen" value="13"/>
                <option label="Fourteen" value="14"/>
                <option label="Fifteen" value="15"/>
                <option label="Sixteen" value="16"/>
                <option label="Seventeen" value="17"/>
                <option label="Eighteen" value="18"/>
                <option label="Nineteen" value="19"/>
                <option label="Twenty" value="20"/>
            </options>
        </param>
        <param field="Mode6" label="Debug" width="150px">
            <options>
                <option label="None" value="0"  default="true" />
                <option label="Python Only" value="2"/>
                <option label="Basic Debugging" value="62"/>
                <option label="Basic+Messages" value="126"/>
                <option label="Queue" value="128"/>
                <option label="Connections Only" value="16"/>
                <option label="Connections+Queue" value="144"/>
                <option label="All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import encoder

class BasePlugin:

    CMD_GET_FIRMWARE_VERSION = "g-fv"
    CMD_SET_OUTPUT_POWER = "s-op"
    CMD_EXECUTE_TX = "e-tx "
    COMMAND_RESULT_OK = "OK"

    InitCommands = [
        "s-mt 1",          # set modulation type OOK
        "s-fd 0",          # set frequency deviation 0
        "s-f 433920000",   # set frequency 433.92 Mhz
        "s-rxbw 20",       # set rx bw to 125 khz
        "s-br 4800",       # set baud rate 4800
        "s-ps 0",          # set preamble size 0
        "s-se 0",          # set sync enable off
        "s-ss 0",          # set sync size 0
        "s-sbe 0",         # Set sync bit errors to 0
        "s-pf 1",          # Set packet format to variable
        "s-crc 0",         # Set crc off
        "s-caco 0",        # Set crc auto clear off
        "s-af 0",           # Set address filter off
        "s-op"
    ]

    LastCommand = ""
    CommandIndex = 0
    SerialConn = None
    IsInitalised = False

    SwitchingCommand = ""
    IsSwitching = False
    UnitSwitchingId = 0

    def __init__(self):
        return

    def onStart(self):
        if Parameters["Mode6"] != "0":
            Domoticz.Debugging(int(Parameters["Mode6"]))
            DumpConfigToLog()
        
        homeAddresses = Parameters["Mode1"].split(";")

        Domoticz.Status("[{0}] HomeAddresses [{1}] Devices"
                        .format(str(len(homeAddresses)), str(len(Devices))))

        deviceCount = len(Devices)

        # Can have up too 5 switches per home address, Switch ALL, 1, 2, 3, 4
        if(deviceCount < len(homeAddresses) * 5):
            Domoticz.Debug("Creating Devices")
            self.add_devices(len(homeAddresses))
            Domoticz.Debug("Created {} Devices", str(len(Devices) - deviceCount))

        for Device in Devices:
            Devices[Device].Update(
                nValue=Devices[Device].nValue, sValue=Devices[Device].sValue)

        SerialConn = Domoticz.Connection(Name="Serial Connection", Transport="Serial",
                                         Protocol="None", Address=Parameters["SerialPort"], Baud=230400)
        SerialConn.Connect()

    def onStop(self):
        Domoticz.Debug("onStop called")

    def onConnect(self, Connection, Status, Description):
        if (Status == 0):
            Domoticz.Status("Connected successfully to: {}"
                            .format(Parameters["SerialPort"]))

            self.SerialConn = Connection
            self.send_command(self.CMD_GET_FIRMWARE_VERSION)
        else:
            Domoticz.Error("Failed to connect to: {0} Status: {1} Description: {2}"
                           .format(Parameters["SerialPort"], str(Status), Description))
        return True

    def onMessage(self, Connection, Data):
        strData = Data.decode("ascii")
        strData = strData.replace("\n", "")

        Domoticz.Debug("Command Executed: [{0}] Response: [{1}]"
                       .format(self.LastCommand,strData))

        if(self.IsInitalised == False):
            if(self.LastCommand.startswith(self.CMD_GET_FIRMWARE_VERSION)):
                Domoticz.Status("Rfm Firmware Version: {}"
                                .format(strData))

            if(self.CommandIndex < len(self.InitCommands)):
                if(self.InitCommands[self.CommandIndex].startswith(self.CMD_SET_OUTPUT_POWER)):
                    self.send_command(self.CMD_SET_OUTPUT_POWER + " " + str(Parameters["Mode4"]))
                else:
                    self.send_command(self.InitCommands[self.CommandIndex])

                self.CommandIndex = self.CommandIndex + 1
            else:
                Domoticz.Status("Initalised")
                self.LastCommand = ""
                self.IsInitalised = True
        else:
            if(self.IsSwitching == True and self.LastCommand.startswith(self.CMD_EXECUTE_TX)):
                Domoticz.Status("Setting Switch State: {}"
                                .format(str(self.SwitchingCommand)))
                if(self.SwitchingCommand == "On"):
                    self.update_device(self.UnitSwitchingId, 1, "100")
                else:
                    self.update_device(self.UnitSwitchingId, 0, "0")
                self.IsSwitching = False

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit: {0} Command: {1} Parameter: {2} Level: {2} Hue: {3}"
                       .format(Unit, Command, str(Level), str(Hue)))

        if(self.IsInitalised == True and self.IsSwitching == False):
            Domoticz.Status("Switching [{0}] Command [{1}]"
                            .format(Unit, Command))

            homeAddress = self.determine_device_home_address(Unit)
            deviceAddress = Unit % 5

            self.IsSwitching = True
            self.UnitSwitchingId = Unit
            self.SwitchingCommand = Command
            
            switchMessageBytes = encoder.build_switch_msg(
                Command == "On", deviceAddress - 1, int(homeAddress, base=16))

            switchMessage = str(''.join(format(x, '02x') for x in switchMessageBytes))

            self.send_command(
                "{0} {1} {2} {3}"
                .format(self.CMD_EXECUTE_TX, switchMessage, Parameters["Mode5"], Parameters["Mode3"]))
        else:
            if(self.IsInitalised == False):
                Domoticz.Debug("Not initalised")
            else:
                Domoticz.Debug("Switching in progress")

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("Connection {} disconnected."
                       .format(Connection))
        return

    def onHeartbeat(self):
        pass

    # Support functions
    def send_command(self, Command):
        self.LastCommand = Command
        self.SerialConn.Send(Command + "\n")

    def add_devices(self, Index):
        prefix = ord('A')

        for i in range(Index):
            for y in range(5):
                unitId = (i * 5) + y
                if((unitId % 5) == 0):
                    Domoticz.Debug("Creating Device [Home {} Switch ALL]"
                                   .format(chr(prefix)))
                    Domoticz.Device(Name="Home "+chr(prefix)+" Switch ALL", Unit=unitId+1,
                                    TypeName="Switch", Type=244, Subtype=62, Switchtype=0).Create()
                else:
                    Domoticz.Debug("Creating Device [Home {0} Switch {1}]"
                                   .format(chr(prefix), str(y)))
                    Domoticz.Device(Name="Home "+chr(prefix)+" Switch "+str(y), Unit=unitId+1,
                                    TypeName="Switch", Type=244, Subtype=62, Switchtype=0).Create()

            prefix = prefix + 1

    def update_device(self, UnitId, nValue, sValue):
        for x in Devices:
            if(Devices[x].ID == UnitId):
                Devices[x].Update(nValue=nValue, sValue=str(sValue))
                Domoticz.Status("Updated Device: {0} Name: {1} State: {2}"
                                .format(str(UnitId), Devices[x].Name, sValue))

    def determine_device_home_address(self, Unit):
        homeAddress = ""

        homeAddresses = Parameters["Mode1"].split(";")

        homeAddressIndex = (Unit-1) // 5

        if(homeAddressIndex > len(homeAddresses)):
            Domoticz.Error("No Home Address could be found for Unit: {}"
                           .format(str(Unit)))
        else:
            homeAddress = homeAddresses[homeAddressIndex]
            Domoticz.Status("Home Address Found for Unit: {0} HomeAddress: {1}"
                            .format( str(Unit), str(homeAddress)))

        return homeAddress


global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status,
                           Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug("'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return