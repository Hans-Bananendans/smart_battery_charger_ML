# -*- coding: utf-8 -*-
"""
Kasper De Smaele

This script  is an example of how to use the battery SOC estimation function 
"""

from EstimationFunction import estimateCapacity

#simulated inputs
voltage = 4.01 #V
current = 2.62 #A
temperature = 283.4 #K
nom_capacity = 2.3 #Ah
charging = False

print(estimateCapacity(current, voltage, temperature, nom_capacity, charging))
