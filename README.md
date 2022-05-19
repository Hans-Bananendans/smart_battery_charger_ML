# smart_battery_charger_ML
Codebase for scripts used in a Li-ion battery charger embedded system that estimates capacity using machine learning.

##
>> "Help! Where did my stuff go??"

The code is divided over the repository in the following way:
 - _/Capacity\_Model/\*_ contains all code_ related to the training of the **capacity estimation ML model**.
 - _/Control\_software/microcontroller/\*_ contains all **code for the microcontroller** (Pico) to correctly run the smart battery charger system.
 - _/Control\_software/pc\_client/\*_ contains all **code for the pc slave** running the capacity model inference.
 - _/OLED\_custom\_firmware/\*_ contains custom firmware to run the OLED screen.
 - _/Legacy code/\*_ is a temporary location to store old code.
