# Discourse_null7b
# Autor: Richarde
# Script zum Update eines Discourse-Forum-Posts via User "Ampel-Bot"
# wird mindestens einer von 3 Eingängen geschalten, geht die Ampel auf Grün
# ist kein Eingang High, geht die Ampel auf Rot (since V1.1 this logic is reverse)
# Version 1.1 vom 04.08.2021
###############################################################################
# ChangeLog:
###############################################################################
# Version 1.0 - 21.07.2021
# Richarde
# Initiale Version 
###############################################################################
# Version 1.1 - 04.08.2021
# Richarde
# - Logikumkehr: Es soll ein Eingang am Raspi auf Masse geschalten werden wenn 
#   eine der Überwachten Sicherungen eingeschalten wird, somit keine falschen
#   Schaltvorgänge durch Induktionsspannungen (Schaltpegel 3,3 V ist sehr klein) 
# - Schaltverzögerung von 2 Sekunden um jedes Prellen der Schalter zu vermeiden


# benötigte Bibliotheken für das Projekt einbinden
from pydiscourse import DiscourseClient
import RPi.GPIO as GPIO
import datetime
import pytz
import constants
import time
import locale

# Klassendefinition
class null7b:
    # CLASSDATA
    __instance = None   # Singleton

    # CONSTANTS
    JA = 'ja'
    NEIN = 'nein'
    ROT = 'rot'
    GRN = 'grn'

    def __new__(cls):
        if not null7b.__instance:
            null7b.__instance = object.__new__(null7b)
        return cls.__instance

    def __init__(self):
        self.jemand_da = self.NEIN
        self.ampel_status = self.ROT

    def update_ampel(self, i_setze_auf): 
        
        l_zone_ber = pytz.timezone('Europe/Berlin')
        l_date_ber = datetime.datetime.now(l_zone_ber)
        l_format = "%a %d.%m.%Y - %H:%M:%S"
        l_ts_string = l_date_ber.strftime(l_format)

        l_content_red = constants.content_red.replace("<Platz für Timestamp>", l_ts_string)
        l_content_grn = constants.content_grn.replace("<Platz für Timestamp>", l_ts_string)

        l_client = DiscourseClient(
                constants.forum_address,
                api_username = constants.api_username,
                api_key = constants.api_key,)

        if i_setze_auf == self.GRN:
            l_client.update_post( constants.post_id, l_content_grn, constants.edit_reason )
        elif i_setze_auf == self.ROT:
            l_client.update_post( constants.post_id, l_content_red, constants.edit_reason )


    def main(self):

        l_count = 1      
        
        while True: #running forever
            # Gerüst vorerst für 3 Eingänge (5, 24, 25), kann aber auf bis zu 17 erweitert werden
            # Version 1.1 - Logikumkehr, 3x Hi == keiner da, min 1x Low == jemand da
            if (not GPIO.input(5) or not GPIO.input(24) or not GPIO.input(25)) and self.jemand_da == self.NEIN:
                l_count = 1
                while l_count <= 4:
                    l_count = l_count + 1
                    time.sleep(0.5) #besser 4x schauen als 1x, verringert das Risiko einer Fehlbetätigung bei flatternden Zuständen nochmals
                    if l_count == 4 and (not GPIO.input(5) or not GPIO.input(24) or not GPIO.input(25)):
                        # ok, getting serious... switch it!
                        self.jemand_da = self.JA
                    elif not GPIO.input(5) or not GPIO.input(24) or not GPIO.input(25):
                        continue # next iteration
                    else:
                        break # leave while
            
            elif (GPIO.input(5) and GPIO.input(24) and GPIO.input(25)) and self.jemand_da == self.JA:
                l_count = 0
                while l_count <= 4:
                    l_count = l_count + 1
                    time.sleep(0.5) #besser 4x schauen als 1x, verringert das Risiko einer Fehlbetätigung bei flatternden Zuständen nochmals
                    if l_count == 4 and (GPIO.input(5) and GPIO.input(24) and GPIO.input(25)):
                        # ok, getting serious... switch it!
                        self.jemand_da = self.NEIN
                    elif GPIO.input(5) and GPIO.input(24) and GPIO.input(25):
                        continue # next iteration
                    else:
                        break # leave while

            if self.ampel_status == self.ROT and self.jemand_da == self.JA:
                self.ampel_status = self.GRN
                self.update_ampel( self.ampel_status )
            elif self.ampel_status == self.GRN and self.jemand_da == self.NEIN:
                self.ampel_status = self.ROT
                self.update_ampel( self.ampel_status )
            #else:
                # wenn rot und keiner da
                # oder
                # grün und jemand da
                    # do nothing

            # Forums-posts können nicht zu schnell hintereinander geändert werden
            # ohne Wartezeit kann es zu Fehlern kommen
            time.sleep(10) #10 Sekunden warten... 


############################################################################################
#Start Program

# Umstellung auf Deutsch für Wochentagsausgabe im Datumstring
locale.setlocale(locale.LC_ALL, 'de_DE.utf8')

#SetUp GPIO PINs as Input
GPIO.setmode(GPIO.BCM)  # GPIO Nummerierung statt Pin Nummerierung
GPIO.setup(5, GPIO.IN)  # set GPIO  5 as input  
GPIO.setup(24, GPIO.IN) # set GPIO 24 as input  
GPIO.setup(25, GPIO.IN) # set GPIO 25 as input  

g_null7b = null7b()
g_null7b.main()