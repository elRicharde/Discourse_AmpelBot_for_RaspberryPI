# Discourse_AmpelBot_for_RaspberryPI
 Python Script for Raspberry PI which uses 3 Inputs to Update a Post in Dsicourse like a Crosslight (Redlight or Greenlight)

This script is for running on a RaspiPi and will check 3 Inputs. Wheather the 3 Inputs are HiLevel the Bot sends a Update to a Discourse Post as an Edit (red Light), if at least one Input is low then the Bot sends Green light as Update to the Forum. 

With Version 1.1 the Logic was switched to 3x HiLevel = RedLight, at least one LowLevel = GreenLight, which has better resistance against false switching 

Several Waits in Coding avoid unclear states as well. 

Version 1.2 - internal PullUp Resistors switched on

Version 1.3 - Auswertungen der Sicherungen nun zusätzlich zur Ampel und ebenfalls mit Timestamp im Post

Version 1.3 - small Bugfixes