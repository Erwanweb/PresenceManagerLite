#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ATemporized presence detection plugin
# Author: MrErwan,
# Version:    0.0.1: alpha...

"""
<plugin key="PresenceManagerLite" name="Ronelabs- Presence Manager Lite" author="Erwanweb" version="1.1.0">
    <params>
        <param field="Mode1" label="IDX capteurs (séparés par des virgules)" width="400px" required="true" />
        <param field="Mode2" label="IDX relais à contrôler (séparés par des virgules)" width="400px" required="true" />
        <param field="Mode3" label="Temporisation présence (s)" width="100px" required="true" default="5"/>
        <param field="Mode4" label="Temporisation absence (s)" width="100px" required="true" default="60"/>
    </params>
</plugin>
"""

import Domoticz
import time

class BasePlugin:
    def __init__(self):
        self.presence_sensors = []
        self.relay_outputs = []
        self.presence_on_delay = 2
        self.presence_off_delay = 30
        self.presence_detected = False
        self.presence_start_time = None
        self.absence_start_time = None

    def onStart(self):
        Domoticz.Log("Plugin démarré")
        self.presence_sensors = list(map(int, Parameters["Mode1"].split(",")))
        self.relay_outputs = list(map(int, Parameters["Mode2"].split(",")))
        self.presence_on_delay = float(Parameters["Mode3"]) * 60
        self.presence_off_delay = float(Parameters["Mode4"]) * 60
        self.presence_detected = False
        self.presence_start_time = None
        self.absence_start_time = time.time()

        if 1 not in Devices:
            Domoticz.Device(Name="Presence", Unit=1, TypeName="Motion Sensor", Used=1).Create()
            Domoticz.Log("Device 'Presence' (Motion Sensor) créé")

        Domoticz.Heartbeat(10)  # Vérification chaque 10 seconde

    def onHeartbeat(self):
        now = time.time()
        any_sensor_active = any(
            Devices[idx].nValue == 1 for idx in self.presence_sensors if idx in Devices
        )

        if any_sensor_active:
            if not self.presence_detected:
                if self.presence_start_time is None:
                    self.presence_start_time = now
                    Domoticz.Debug("Début du délai de présence")
                elif now - self.presence_start_time >= self.presence_on_delay:
                    self.setPresence(True)
            else:
                self.absence_start_time = None
        else:
            if self.presence_detected:
                if self.absence_start_time is None:
                    self.absence_start_time = now
                    Domoticz.Debug("Début du délai d'absence")
                elif now - self.absence_start_time >= self.presence_off_delay:
                    self.setPresence(False)
            else:
                self.presence_start_time = None

    def setPresence(self, state):
        self.presence_detected = state
        action = "Présence détectée" if state else "Absence confirmée"
        Domoticz.Log(action)

        # Mettre à jour le widget motion sensor (Device Unit 1)
        if 1 in Devices:
            value = 1 if state else 0
            if Devices[1].nValue != value:
                Devices[1].Update(nValue=value, sValue=str(value))
                Domoticz.Log(f"Widget Présence mis à {'On' if value else 'Off'}")
        else:
            Domoticz.Error("Widget Présence non trouvé")

        # Activer/Désactiver les relais
        for idx in self.relay_outputs:
            if idx in Devices:
                value = 1 if state else 0
                if Devices[idx].nValue != value:
                    Domoticz.Device(Unit=idx).Update(nValue=value, sValue=str(value))
                    Domoticz.Log(f"Relais {idx} mis à {'On' if value else 'Off'}")
            else:
                Domoticz.Log(f"IDX {idx} non trouvé dans Devices")

    def onCommand(self, Unit, Command, Level, Color):
        Domoticz.Debug(f"Command reçue: {Command}")

global _plugin
_plugin = BasePlugin()

def onStart():
    _plugin.onStart()

def onHeartbeat():
    _plugin.onHeartbeat()

def onCommand(Unit, Command, Level, Color):
    _plugin.onCommand(Unit, Command, Level, Color)
