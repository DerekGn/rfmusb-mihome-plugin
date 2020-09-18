# Python plugin for controlling energenie OOK devices
#
# Author: DerekGn
#
"""
<plugin key="RfmEnergOok" name="RfmUsb Energenie OOK" author="DerekGn" version="1.0.0" wikilink="http://www.domoticz.com/wiki/plugins/plugin.html" externallink="https://github.com/DerekGn/rfmusb-mihome-ook-plugin">
    <description>
        <h2>RfmUsb Energenie Ook Devices Plugin</h2>
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
        Serial port is the name of the 
    </description>
    <params>
        <param field="SerialPort" label="Serial Port" width="150px" required="true" default="/dev/serial1"/>
        <param field="Mode1" label="Home Addresses" width="300px" required="true" default="6C6C6"/>
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
                <option label="Five" value="5"/>
                <option label="Eight" value="8"/>
                <option label="Thirteen" value="13"/>
            </options>
        </param>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import encoder
import binascii

class BasePlugin:

    CMD_SET_STBY_MODE_COMMAND = "s-om 0"
    CMD_SET_TX_MODE_COMMAND = "s-om 3"
    CMD_GET_FIRMWARE_VERSION = "g-fv"
    COMMAND_RESULT_OK = "OK"

    InitCommands = [
        "e-r",
        "s-mt 1",
        "s-fd 0",
        "s-f 433920000",
        "s-br 4800",
        "s-ps 0",
        "s-se 0",
        "s-ss 0",
        "s-sbe 0",
        "s-pf 1",
        "s-cc 0",
        "s-caco 0",
        "s-af 0",
        "s-dio 0 1",
        "s-di 1"
    ]

    LastCommand = ""
    CommandIndex = 0
    SerialConn = None
    IsInitalised = False

    SwitchMessageCount = 0
    SwitchingCommand = ""
    SwitchMessage = []
    SwitchingUnit = None
    IsSwitching = False

    def __init__(self):
        #self.var = 123
        return

    def onStart(self):
        homeAddresses = Parameters["Mode1"].split(";")

        Domoticz.Log("["+str(len(homeAddresses)) +
                     "] HomeAddresses ["+str(len(Devices))+"] Devices")

        deviceCount = len(Devices)

        # Can have up too 5 switches per home address, Switch ALL, 1, 2, 3, 4
        if(deviceCount < len(homeAddresses) * 5):
            Domoticz.Log("Creating Devices")
            self.AddDevices(len(homeAddresses))
            Domoticz.Log("Created "+str(len(Devices) - deviceCount)+" Devices")

        for Device in Devices:
            Devices[Device].Update(
                nValue=Devices[Device].nValue, sValue=Devices[Device].sValue)

        SerialConn = Domoticz.Connection(Name="Serial Connection", Transport="Serial",
                                         Protocol="None", Address=Parameters["SerialPort"], Baud=115200)
        SerialConn.Connect()

    def onStop(self):
        Domoticz.Log("onStop called")

    def onConnect(self, Connection, Status, Description):
        if (Status == 0):
            Domoticz.Log("Connected successfully to: " +
                         Parameters["SerialPort"])

            self.SerialConn = Connection
            self.SendCommand(self.CMD_GET_FIRMWARE_VERSION)
        else:
            Domoticz.Log("Failed to connect ("+str(Status) +
                         ") to: "+Parameters["SerialPort"])

            Domoticz.Debug("Failed to connect ("+str(Status)+") to: " +
                           Parameters["SerialPort"]+" with error: "+Description)
        return True

    def onMessage(self, Connection, Data):
        strData = Data.decode("ascii")
        strData = strData.replace("\n", "")

        Domoticz.Log(
            "Command Executed: ["+self.LastCommand+"] Respose: ["+strData+"] ")

        if(self.IsInitalised == False):
            if(self.CommandIndex < len(self.InitCommands)):
                self.SendCommand(self.InitCommands[self.CommandIndex])
                self.CommandIndex = self.CommandIndex + 1
            else:
                self.IsInitalised = True

        if(self.IsSwitching == True):
            if(self.SwitchMessageCount < int(Parameters["Mode5"])):
                Domoticz.Log("["+str(self.SwitchMessageCount)+"]Sending Switch Message: ["+str(self.SwitchMessage)+"]")
                self.SendCommand("s-fifo " + binascii.hexlify(bytearray(self.SwitchMessage)))
                self.SwitchMessageCount = self.SwitchMessageCount + 1
            else:
                if(self.SwitchingCommand == "On"):
                    self.UpdateDevice(self.SwitchingUnit, 1, "100")
                else:
                    self.UpdateDevice(self.SwitchingUnit, 0, "0")
                self.SwitchingUnit = None
                self.IsSwitching = False
                self.SendCommand(self.CMD_SET_STBY_MODE_COMMAND)

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) +
                     ": Parameter '" + str(Command) + "', Level: " + str(Level))

        if(self.IsInitalised == True and self.IsSwitching == False):
            homeAddress = self.DetermineDeviceHomeAddress(Unit)
            deviceAddress = Unit % 5
            
            self.SwitchMessage = encoder.build_switch_msg(Command == "On", deviceAddress ,int(homeAddress, base=16))
            self.SwitchMessageCount = 0
            self.UnitSwitching = Unit
            self.IsSwitching = True
            self.SwitchingCommand = Command

            # enable Tx mode
            self.SendCommand(self.CMD_SET_TX_MODE_COMMAND)
            Domoticz.Log("Started Executing Switching ["+str(Unit)+"] Command["+Command+"]")
        else:
            if(self.IsInitalised == False):
                Domoticz.Log("Not initalised")
            else:
                Domoticz.Log("Switching in progress")

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text +
                     "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("Connection '"+Connection.Name+"' disconnected.")
        return

    def onHeartbeat(self):
        pass

    # Support functions
    def SendCommand(self, Command):
        self.LastCommand = Command
        self.SerialConn.Send(Command + "\n")

    def AddDevices(self, Index):
        prefix = ord('A')

        for i in range(Index):
            for y in range(5):
                unitId = (i * 5) + y
                if((unitId % 5) == 0):
                    Domoticz.Log(
                        "Creating Device [Home "+chr(prefix)+" Switch ALL]")
                    Domoticz.Device(Name="Home "+chr(prefix)+" Switch ALL", Unit=unitId+1,
                                    TypeName="Switch", Type=244, Subtype=62, Switchtype=0).Create()
                else:
                    Domoticz.Log(
                        "Creating Device [Home "+chr(prefix)+" Switch "+str(y)+"]")
                    Domoticz.Device(Name="Home "+chr(prefix)+" Switch "+str(y), Unit=unitId+1,
                                    TypeName="Switch", Type=244, Subtype=62, Switchtype=0).Create()

            prefix = prefix + 1

    def UpdateDevice(self, Unit, nValue, sValue):
        # Make sure that the Domoticz device still exists (they can be deleted) before updating it
        if (Unit in Devices):
            if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue):
                Devices[Unit].Update(nValue=nValue, sValue=str(sValue))
                Domoticz.Log("Update "+str(nValue)+":'" +
                             str(sValue)+"' ("+Devices[Unit].Name+")")
            return

    def DetermineDeviceHomeAddress(self, Unit):
        homeAddress = ""

        homeAddresses = Parameters["Mode1"].split(";")

        homeAddressIndex = (Unit-1) // 5

        if(homeAddressIndex > len(homeAddresses)):
            Domoticz.Log(
                "No Home Address could be found for Unit:" + str(Unit))
        else:
            homeAddress = homeAddresses[homeAddressIndex]
            Domoticz.Log("Home Address Found for Unit:" + str(Unit) + "HomeAddress: ["+ str(homeAddress)+"]")
            
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

    # Generic helper functions


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
