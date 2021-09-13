# Discourse_null7b
# Autor: Richarde
# Script zum Update eines Discourse-Forum-Posts via User "Ampel-Bot"
# wird mindestens einer von 3 Eingängen geschalten, geht die Ampel auf Gruen
# ist kein Eingang High, geht die Ampel auf Rot
# Version 1.1 vom 04.08.2021
#
#   GPIO.input(5)  = grün = Sicherung F7 - Dj Rot Std. (Dj-Pult)
#   GPIO.input(24) = grün/weiß = Sicherung F13 - Kasse
#   GPIO.input(25) = braun = Sicherung F15 - Bar Theke 
#
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
#   eine der berwachten Sicherungen eingeschalten wird, somit keine falschen
#   Schaltvorgänge durch Induktionsspannungen (Schaltpegel 3,3 V ist sehr klein) 
# - Schaltverzögerung von 2 Sekunden um jedes Prellen der Schalter zu vermeiden
###############################################################################
# Version 1.2 - 07.09.2021
# Richarde
# - interne Vorwiderstände aufschalten
###############################################################################
# Version 1.3 - 11.09.2021
# Richarde
# einzelne Auswertung der Sicherungen zusätzlich zum Hallenstatus
###############################################################################
# Version 1.31 - 11.09.2021
# Richarde
# Bugfixes
###############################################################################
# Version 1.32 - 13.09.2021
# Richarde
# Bugfixes
###############################################################################


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
    ROT = 'rot'
    GRN = 'grn'
    AN = 'an'
    AUS = 'aus'

    def __new__(cls):
        if not null7b.__instance:
            null7b.__instance = object.__new__(null7b)
        return cls.__instance

    def __init__(self):
        self.ampel_status = self.ROT
        self.f7_forum = 'xxx'
        self.f13_forum = 'xxx'
        self.f15_forum = 'xxx'  #somit wird bei Programmstart immer ein Post abgesetzt

        self.zone_ber = pytz.timezone('Europe/Berlin')
        self.date_ber = datetime.datetime.now(self.zone_ber)
        self.format = "%a %d.%m.%Y - %H:%M:%S"

        self.datetimestring_ampel = self.date_ber.strftime(self.format)
        self.datetimestring_f7 = self.date_ber.strftime(self.format)
        self.datetimestring_f13 = self.date_ber.strftime(self.format)
        self.datetimestring_f15 = self.date_ber.strftime(self.format)

        if GPIO.input(5):
            self.f7_dj = self.AUS
        else:
            self.f7_dj = self.AN

        if GPIO.input(24):
            self.f13_kasse = self.AUS
        else:
            self.f13_kasse = self.AN

        if GPIO.input(25):
            self.f15_bar_theke_licht = self.AUS            
        else:
            self.f15_bar_theke_licht = self.AN      

    def get_datetimestring(self): 
        
        l_zone_ber = pytz.timezone('Europe/Berlin')
        l_date_ber = datetime.datetime.now(l_zone_ber)
        l_format = "%a %d.%m.%Y - %H:%M:%S"
        l_ts_string = l_date_ber.strftime(l_format)
        return l_ts_string

    def update_ampel(self, i_setze_auf): 

        l_content_red = constants.content_red.replace("<datetimestring_ampel>", self.datetimestring_ampel)
        l_content_red = l_content_red.replace("<datetimestring_f7>", self.datetimestring_f7)
        l_content_red = l_content_red.replace("<datetimestring_f13>", self.datetimestring_f13)
        l_content_red = l_content_red.replace("<datetimestring_f15>", self.datetimestring_f15)
        l_content_red = l_content_red.replace("<F7>", self.f7_dj)
        l_content_red = l_content_red.replace("<F13>", self.f13_kasse)
        l_content_red = l_content_red.replace("<F15>", self.f15_bar_theke_licht)

        l_content_grn = constants.content_grn.replace("<datetimestring_ampel>", self.datetimestring_ampel)
        l_content_grn = l_content_grn.replace("<datetimestring_f7>", self.datetimestring_f7)
        l_content_grn = l_content_grn.replace("<datetimestring_f13>", self.datetimestring_f13)
        l_content_grn = l_content_grn.replace("<datetimestring_f15>", self.datetimestring_f15)
        l_content_grn = l_content_grn.replace("<F7>", self.f7_dj)
        l_content_grn = l_content_grn.replace("<F13>", self.f13_kasse)
        l_content_grn = l_content_grn.replace("<F15>", self.f15_bar_theke_licht)

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

            #F7 prüfen
            if self.f7_dj == self.AN:      #F7 ist an
                l_count = 0
                while l_count < 4: #4 Durchgänge
                    l_count = l_count + 1
                    time.sleep(0.5) #besser 4x schauen als 1x, verringert das Risiko einer Fehlbetätigung bei flatternden Zuständen nochmals
                    if GPIO.input(5) and l_count == 4:      #F7 ist 2 Sekunden lang aus
                        # ok, getting serious... switch it!
                        self.f7_dj = self.AUS
                    if GPIO.input(5):                       #F7 ist aus
                        continue # next iteration
                    else:   #F7 ist an
                        break # leave while
            elif self.f7_dj == self.AUS:    #F7 ist aus
                l_count = 0
                while l_count < 4: #4 Durchgänge
                    l_count = l_count + 1
                    time.sleep(0.5) #besser 4x schauen als 1x, verringert das Risiko einer Fehlbetätigung bei flatternden Zuständen nochmals
                    if not GPIO.input(5) and l_count == 4:      #F7 ist 2 Sekunden lang an
                        # ok, getting serious... switch it!
                        self.f7_dj = self.AN
                    if not GPIO.input(5):           #F7 ist an
                        continue # next iteration
                    else:    #F7 ist aus
                        break # leave while

            #F13 prüfen
            if self.f13_kasse == self.AN:      #F13 ist an
                l_count = 0
                while l_count < 4: #4 Durchgänge
                    l_count = l_count + 1
                    time.sleep(0.5) #besser 4x schauen als 1x, verringert das Risiko einer Fehlbetätigung bei flatternden Zuständen nochmals
                    if GPIO.input(24) and l_count == 4:      #F13 ist 2 Sekunden lang aus
                        # ok, getting serious... switch it!
                        self.f13_kasse = self.AUS
                    if GPIO.input(24):                       #F13 ist aus
                        continue # next iteration
                    else:   #F13 ist an
                        break # leave while
            elif self.f13_kasse == self.AUS:    #F13 ist aus
                l_count = 0
                while l_count < 4: #4 Durchgänge
                    l_count = l_count + 1
                    time.sleep(0.5) #besser 4x schauen als 1x, verringert das Risiko einer Fehlbetätigung bei flatternden Zuständen nochmals
                    if not GPIO.input(24) and l_count == 4:      #F13 ist 2 Sekunden lang an
                        # ok, getting serious... switch it!
                        self.f13_kasse = self.AN
                    if not GPIO.input(24):           #F13 ist an
                        continue # next iteration
                    else:    #F13 ist aus
                        break # leave while

            #F15 prüfen
            if self.f15_bar_theke_licht == self.AN: #F15 ist an
                l_count = 0
                while l_count < 4: #4 Durchgänge
                    l_count = l_count + 1
                    time.sleep(0.5) #besser 4x schauen als 1x, verringert das Risiko einer Fehlbetätigung bei flatternden Zuständen nochmals
                    if GPIO.input(25) and l_count == 4:      #F15 ist 2 Sekunden lang aus
                        # ok, getting serious... switch it!
                        self.f15_bar_theke_licht = self.AUS
                    if GPIO.input(25):                       #F15 ist aus
                        continue # next iteration
                    else:   #F15 ist an
                        break # leave while
            elif self.f15_bar_theke_licht == self.AUS:    #F15 ist aus
                l_count = 0
                while l_count < 4: #4 Durchgänge
                    l_count = l_count + 1
                    time.sleep(0.5) #besser 4x schauen als 1x, verringert das Risiko einer Fehlbetätigung bei flatternden Zuständen nochmals
                    if not GPIO.input(25) and l_count == 4:      #F15 ist 2 Sekunden lang an
                        # ok, getting serious... switch it!
                        self.f15_bar_theke_licht = self.AN
                    if not GPIO.input(25):           #F15 ist an
                        continue # next iteration
                    else:    #F15 ist aus
                        break # leave while

            
            #Hat sich was geändert?
            # 3 Änderungen
            if self.f7_dj != self.f7_forum and self.f13_kasse != self.f13_forum and self.f15_bar_theke_licht != self.f15_forum:
                self.datetimestring_f7 = self.get_datetimestring()
                self.datetimestring_f13 = self.datetimestring_f7
                self.datetimestring_f15 = self.datetimestring_f7
                self.f7_forum = self.f7_dj
                self.f13_forum = self.f13_kasse
                self.f15_forum = self.f15_bar_theke_licht

                if ( self.f7_dj == self.AN or self.f13_kasse == self.AN or self.f15_bar_theke_licht == self.AN ) and self.ampel_status == self.ROT:     #Änderung Ampel rot -> grün
                    self.datetimestring_ampel = self.datetimestring_f7
                    self.ampel_status = self.GRN
                    self.update_ampel( self.ampel_status )                    

                elif self.f7_dj == self.AUS and self.f13_kasse == self.AUS and self.f15_bar_theke_licht == self.AUS and self.ampel_status == self.GRN:   #Änderung Ampel grün -> rot
                    self.datetimestring_ampel = self.datetimestring_f7
                    self.ampel_status = self.ROT
                    self.update_ampel( self.ampel_status )   

                elif ( self.f7_dj == self.AN or self.f13_kasse == self.AN or self.f15_bar_theke_licht == self.AN ) and self.ampel_status == self.GRN:     #Ampel ist und bleibt grün
                    self.update_ampel( self.ampel_status )    

                elif self.f7_dj == self.AUS and self.f13_kasse == self.AUS and self.f15_bar_theke_licht == self.AUS and self.ampel_status == self.ROT:   #Ampel ist und bleibt rot
                    self.update_ampel( self.ampel_status )  

            # 2 Änderungen F7 & F13
            elif self.f7_dj != self.f7_forum and self.f13_kasse != self.f13_forum:
                self.datetimestring_f7 = self.get_datetimestring()
                self.datetimestring_f13 = self.datetimestring_f7
                self.f7_forum = self.f7_dj
                self.f13_forum = self.f13_kasse

                if ( self.f7_dj == self.AN or self.f13_kasse == self.AN or self.f15_bar_theke_licht == self.AN ) and self.ampel_status == self.ROT:     #Änderung Ampel rot -> grün
                    self.datetimestring_ampel = self.datetimestring_f7
                    self.ampel_status = self.GRN
                    self.update_ampel( self.ampel_status )                    

                elif self.f7_dj == self.AUS and self.f13_kasse == self.AUS and self.f15_bar_theke_licht == self.AUS and self.ampel_status == self.GRN:   #Änderung Ampel grün -> rot
                    self.datetimestring_ampel = self.datetimestring_f7
                    self.ampel_status = self.ROT
                    self.update_ampel( self.ampel_status )   

                elif ( self.f7_dj == self.AN or self.f13_kasse == self.AN or self.f15_bar_theke_licht == self.AN ) and self.ampel_status == self.GRN:     #Ampel ist und bleibt grün
                    self.update_ampel( self.ampel_status )    

                elif self.f7_dj == self.AUS and self.f13_kasse == self.AUS and self.f15_bar_theke_licht == self.AUS and self.ampel_status == self.ROT:   #Ampel ist und bleibt rot
                    self.update_ampel( self.ampel_status )  

            # 2 Änderungen F7 & F15
            elif self.f7_dj != self.f7_forum and self.f15_bar_theke_licht != self.f15_forum:
                self.datetimestring_f7 = self.get_datetimestring()
                self.datetimestring_f15 = self.datetimestring_f7
                self.f7_forum = self.f7_dj
                self.f15_forum = self.f15_bar_theke_licht

                if ( self.f7_dj == self.AN or self.f13_kasse == self.AN or self.f15_bar_theke_licht == self.AN ) and self.ampel_status == self.ROT:     #Änderung Ampel rot -> grün
                    self.datetimestring_ampel = self.datetimestring_f7
                    self.ampel_status = self.GRN
                    self.update_ampel( self.ampel_status )                    

                elif self.f7_dj == self.AUS and self.f13_kasse == self.AUS and self.f15_bar_theke_licht == self.AUS and self.ampel_status == self.GRN:   #Änderung Ampel grün -> rot
                    self.datetimestring_ampel = self.datetimestring_f7
                    self.ampel_status = self.ROT
                    self.update_ampel( self.ampel_status )   

                elif ( self.f7_dj == self.AN or self.f13_kasse == self.AN or self.f15_bar_theke_licht == self.AN ) and self.ampel_status == self.GRN:     #Ampel ist und bleibt grün
                    self.update_ampel( self.ampel_status )    

                elif self.f7_dj == self.AUS and self.f13_kasse == self.AUS and self.f15_bar_theke_licht == self.AUS and self.ampel_status == self.ROT:   #Ampel ist und bleibt rot
                    self.update_ampel( self.ampel_status )  

            # 2 Änderungen F13 & F15
            elif self.f13_kasse != self.f13_forum and self.f15_bar_theke_licht != self.f15_forum:
                self.datetimestring_f13 = self.get_datetimestring()
                self.datetimestring_f15 = self.datetimestring_f13
                self.f13_forum = self.f13_kasse
                self.f15_forum = self.f15_bar_theke_licht

                if ( self.f7_dj == self.AN or self.f13_kasse == self.AN or self.f15_bar_theke_licht == self.AN ) and self.ampel_status == self.ROT:     #Änderung Ampel rot -> grün
                    self.datetimestring_ampel = self.datetimestring_f7
                    self.ampel_status = self.GRN
                    self.update_ampel( self.ampel_status )                    

                elif self.f7_dj == self.AUS and self.f13_kasse == self.AUS and self.f15_bar_theke_licht == self.AUS and self.ampel_status == self.GRN:   #Änderung Ampel grün -> rot
                    self.datetimestring_ampel = self.datetimestring_f7
                    self.ampel_status = self.ROT
                    self.update_ampel( self.ampel_status )   

                elif ( self.f7_dj == self.AN or self.f13_kasse == self.AN or self.f15_bar_theke_licht == self.AN ) and self.ampel_status == self.GRN:     #Ampel ist und bleibt grün
                    self.update_ampel( self.ampel_status )    

                elif self.f7_dj == self.AUS and self.f13_kasse == self.AUS and self.f15_bar_theke_licht == self.AUS and self.ampel_status == self.ROT:   #Ampel ist und bleibt rot
                    self.update_ampel( self.ampel_status )   

            # 1 Änderungen F7
            elif self.f7_dj != self.f7_forum:
                self.datetimestring_f7 = self.get_datetimestring()
                self.f7_forum = self.f7_dj

                if ( self.f7_dj == self.AN or self.f13_kasse == self.AN or self.f15_bar_theke_licht == self.AN ) and self.ampel_status == self.ROT:     #Änderung Ampel rot -> grün
                    self.datetimestring_ampel = self.datetimestring_f7
                    self.ampel_status = self.GRN
                    self.update_ampel( self.ampel_status )                    

                elif self.f7_dj == self.AUS and self.f13_kasse == self.AUS and self.f15_bar_theke_licht == self.AUS and self.ampel_status == self.GRN:   #Änderung Ampel grün -> rot
                    self.datetimestring_ampel = self.datetimestring_f7
                    self.ampel_status = self.ROT
                    self.update_ampel( self.ampel_status )   

                elif ( self.f7_dj == self.AN or self.f13_kasse == self.AN or self.f15_bar_theke_licht == self.AN ) and self.ampel_status == self.GRN:     #Ampel ist und bleibt grün
                    self.update_ampel( self.ampel_status )    

                elif self.f7_dj == self.AUS and self.f13_kasse == self.AUS and self.f15_bar_theke_licht == self.AUS and self.ampel_status == self.ROT:   #Ampel ist und bleibt rot
                    self.update_ampel( self.ampel_status )  

            # 1 Änderung F13
            elif self.f13_kasse != self.f13_forum:
                self.datetimestring_f13 = self.get_datetimestring()
                self.f13_forum = self.f13_kasse

                if ( self.f7_dj == self.AN or self.f13_kasse == self.AN or self.f15_bar_theke_licht == self.AN ) and self.ampel_status == self.ROT:     #Änderung Ampel rot -> grün
                    self.datetimestring_ampel = self.datetimestring_f7
                    self.ampel_status = self.GRN
                    self.update_ampel( self.ampel_status )                    

                elif self.f7_dj == self.AUS and self.f13_kasse == self.AUS and self.f15_bar_theke_licht == self.AUS and self.ampel_status == self.GRN:   #Änderung Ampel grün -> rot
                    self.datetimestring_ampel = self.datetimestring_f7
                    self.ampel_status = self.ROT
                    self.update_ampel( self.ampel_status )   

                elif ( self.f7_dj == self.AN or self.f13_kasse == self.AN or self.f15_bar_theke_licht == self.AN ) and self.ampel_status == self.GRN:     #Ampel ist und bleibt grün
                    self.update_ampel( self.ampel_status )    

                elif self.f7_dj == self.AUS and self.f13_kasse == self.AUS and self.f15_bar_theke_licht == self.AUS and self.ampel_status == self.ROT:   #Ampel ist und bleibt rot
                    self.update_ampel( self.ampel_status )  

            # 1 Änderung F15
            elif self.f15_bar_theke_licht != self.f15_forum:
                self.datetimestring_f15 = self.get_datetimestring()
                self.f15_forum = self.f15_bar_theke_licht

                if ( self.f7_dj == self.AN or self.f13_kasse == self.AN or self.f15_bar_theke_licht == self.AN ) and self.ampel_status == self.ROT:     #Änderung Ampel rot -> grün
                    self.datetimestring_ampel = self.datetimestring_f7
                    self.ampel_status = self.GRN
                    self.update_ampel( self.ampel_status )                    

                elif self.f7_dj == self.AUS and self.f13_kasse == self.AUS and self.f15_bar_theke_licht == self.AUS and self.ampel_status == self.GRN:   #Änderung Ampel grün -> rot
                    self.datetimestring_ampel = self.datetimestring_f7
                    self.ampel_status = self.ROT
                    self.update_ampel( self.ampel_status )   

                elif ( self.f7_dj == self.AN or self.f13_kasse == self.AN or self.f15_bar_theke_licht == self.AN ) and self.ampel_status == self.GRN:     #Ampel ist und bleibt grün
                    self.update_ampel( self.ampel_status )    

                elif self.f7_dj == self.AUS and self.f13_kasse == self.AUS and self.f15_bar_theke_licht == self.AUS and self.ampel_status == self.ROT:   #Ampel ist und bleibt rot
                    self.update_ampel( self.ampel_status )    

            #keine Änderungen
            #else:
                #do nothing, der Post ist gut so wie er ist...


            # Forums-posts können nicht zu schnell hintereinander geändert werden
            # ohne Wartezeit kann es zu Fehlern kommen
            time.sleep(10) #10 Sekunden warten... (kaum noch notwendig, da die 3x 4 Runden schon 6 Sekunden dauern) - aber Schadet auch nix :-)



############################################################################################
#Start Program

# Umstellung auf Deutsch für Wochentagsausgabe im Datumstring
locale.setlocale(locale.LC_ALL, 'de_DE.utf8')

#SetUp GPIO PINs as Input
GPIO.setmode(GPIO.BCM)  # GPIO Nummerierung statt Pin Nummerierung
GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_UP )  # set GPIO  5 as input  
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP ) # set GPIO 24 as input  
GPIO.setup(25, GPIO.IN, pull_up_down=GPIO.PUD_UP ) # set GPIO 25 as input  

g_null7b = null7b()
g_null7b.main()
