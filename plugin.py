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
        <param field="Mode3" label="Temporisation présence (min)" width="100px" required="true" default="0.1"/>
        <param field="Mode4" label="Temporisation absence (min)" width="100px" required="true" default="1"/>
        <param field="Mode6" label="Log Level" width="200px">
            <options>
                <option label="Normal" value="Normal" default="true"/>
                <option label="Debug" value="Debug"/>
            </options>
        </param>
    </params>
</plugin>
"""

import Domoticz
import time

class BasePlugin:
    def __init__(self):
        self.presence_sensors = []
        self.relay_outputs = []
        self.presence_on_delay = 5      # en secondes
        self.presence_off_delay = 60    # en secondes
        self.debug_enabled = False
        self.presence_detected = False
        self.presence_start_time = None
        self.absence_start_time = None

    def log_debug(self, msg):
        if self.debug_enabled:
            Domoticz.Log("[DEBUG] " + msg)

    def onStart(self):
        Domoticz.Log("Plugin démarré")

        try:
            self.presence_sensors = list(map(int, Parameters["Mode1"].split(",")))
            self.relay_outputs = list(map(int, Parameters["Mode2"].split(",")))
        except Exception as e:
            Domoticz.Error("Erreur dans les IDX capteurs/relais : " + str(e))
            return

        # Conversion minutes → secondes
        try:
            self.presence_on_delay = float(Parameters["Mode3"]) * 60
            self.presence_off_delay = float(Parameters["Mode4"]) * 60
        except ValueError:
            Domoticz.Error("Erreur : temporisations invalides.")
            return

        self.debug_enabled = Parameters["Mode6"] == "Debug"

        self.log_debug(f"Capteurs = {self.presence_sensors}")
        self.log_debug(f"Relais = {self.relay_outputs}")
        self.log_debug(f"Temporisation présence = {self.presence_on_delay} s")
        self.log_debug(f"Temporisation absence = {self.presence_off_delay} s")
        self.log_debug(f"Debug activé = {self.debug_enabled}")

        if 1 not in Devices:
            Domoticz.Device(Name="Présence", Unit=1, TypeName="Motion Sensor", Used=1).Create()
            Domoticz.Log("Device 'Présence' (Motion Sensor) créé")

        Domoticz.Heartbeat(20)

    def onHeartbeat(self):
        now = time.time()
        any_sensor_active = any(
            Devices[idx].nValue == 1 for idx in self.presence_sensors if idx in Devices
        )

        self.log_debug(f"État capteurs : {['ON' if Devices[idx].nValue == 1 else 'OFF' for idx in self.presence_sensors if idx in Devices]}")
        self.log_debug(f"Présence détectée ? {any_sensor_active}")

        if any_sensor_active:
            if not self.presence_detected:
                if self.presence_start_time is None:
                    self.presence_start_time = now
                    self.log_debug("Début temporisation présence")
                elif now - self.presence_start_time >= self.presence_on_delay:
                    self.setPresence(True)
            else:
                self.absence_start_time = None
        else:
            if self.presence_detected:
                if self.absence_start_time is None:
                    self.absence_start_time = now
                    self.log_debug("Début temporisation absence")
                elif now - self.absence_start_time >= self.presence_off_delay:
                    self.setPresence(False)
            else:
                self.presence_start_time = None

    def setPresence(self, state):
        self.presence_detected = state
        action = "Présence détectée" if state else "Absence confirmée"
        Domoticz.Log(action)

        # Widget Motion Sensor
        if 1 in Devices:
            value = 1 if state else 0
            if Devices[1].nValue != value:
                Devices[1].Update(nValue=value, sValue=str(value))
                self.log_debug(f"Widget Présence → {'On' if value else 'Off'}")
        else:
            Domoticz.Error("Widget Présence non trouvé")

        # Commande relais
        for idx in self.relay_outputs:
            if idx in Devices:
                value = 1 if state else 0
                if Devices[idx].nValue != value:
                    Domoticz.Device(Unit=idx).Update(nValue=value, sValue=str(value))
                    self.log_debug(f"Relais {idx} → {'On' if value else 'Off'}")
            else:
                Domoticz.Log(f"IDX {idx} non trouvé dans Devices")

    def onCommand(self, Unit, Command, Level, Color):
        self.log_debug(f"Commande reçue : Unit={Unit}, Command={Command}")

global _plugin
_plugin = BasePlugin()

def onStart():
    _plugin.onStart()

def onHeartbeat():
    _plugin.onHeartbeat()

def onCommand(Unit, Command, Level, Color):
    _plugin.onCommand(Unit, Command, Level, Color)
