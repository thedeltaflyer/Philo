#!/usr/bin/python

# Philo's Free Body Simulation
# ----------------------------
# Author: Ara Kourchians
# ----------------------------

import matplotlib
import numpy as np
#import matplotlib.pyplot as plt
import json
import sys
import os.path

# Default Config File
philo_cfg_file = "philo_cfg.json"

# Natural Constants
R = 8.314	# J/(K*mol) or ((Kg*m^2)/s^2)/(K*mol)
g = 9.81	# m/s^2
P_amb = 101325	# Pa
T_amb = 298.15	# K


# Rocket Classes 
class Fuel:
	def __init__(self, fuel_type, cp, cv, molar_mass):
		self.fuel_type = fuel_type
		self.cp = cp				#@ 0.0C
		self.cv = cv				#@ 0.0C
		self.molar_mass = molar_mass
		self.gamma = cp/cv

class Tank:
	def __init__(self, volume, pressure, tank_mass, reg_min, reg_max, temp):
		self.volume = volume		# m^3
		self.pressure = pressure	# Pa
		self.tank_mass = tank_mass	# kg
		self.reg_min = reg_min
		self.reg_max = reg_max
		self.temp = temp 			# K

class Regulator:
	def __init__(self, in_min, in_max, out_min, out_max, reg_set, reg_in, reg_out):
		self.in_min = in_min
		self.in_max = in_max
		self.out_min = out_min
		self.out_max = out_max
		self.reg_set = reg_set
		self.reg_in = reg_in
		self.reg_out = reg_out

class Heater:
	def __init__(self, T_chamber):
		self.T_chamber = T_chamber

class Engine:
	def __init__(self, fuel, P_in, P_ambient, filament):
		self.fuel = fuel
		self.filament = filament
		self.P_in = P_in
		self.P_ambient = P_ambient

		self.V_e = np.sqrt( ((self.filament.T_chamber*R)/self.fuel.molar_mass) \
			   * ((2*self.fuel.gamma)/(self.fuel.gamma-1)) \
			   * ( 1 - (P_ambient/P_in)**( (self.fuel.gamma-1)/self.fuel.gamma ) ) ) 
		self.Isp = self.V_e / g

	def calc_Ve(self):
		"""
			Updates V_e and Isp based on current pressure setting P_in.
			Returns V_e
		"""
		self.V_e = np.sqrt( ((self.filament.T_chamber*R)/self.fuel.molar_mass) \
		   * ((2*self.fuel.gamma)/(self.fuel.gamma-1)) \
		   * ( 1 - (self.P_ambient/self.P_in)**( (self.fuel.gamma-1)/self.fuel.gamma ) ) )

		self.Isp = self.V_e / g
		return self.V_e
		
class Vehicle:
	def __init__(self, avionics_mass, mech_mass, tank, engine, fuel):
		self.avionics_mass = avionics_mass
		self.mech_mass = mech_mass
		self.tank = tank
		self.engine = engine
		self.fuel = fuel
		self.fuel_mass = ((self.tank.pressure * self.tank.volume)/(R*self.tank.temp)) \
				 * self.fuel.molar_mass

		self.dry_mass = self.tank.tank_mass + self.avionics_mass + self.mech_mass
		self.wet_mass = self.dry_mass + self.fuel_mass
		self.veh_mass = self.wet_mass # Initial (wet) condition

		self.Fnull = self.wet_mass * g
		self.mass_flow = self.Fnull/self.engine.V_e


#regulator = {'':
def run_sim(vehicle):
	# Simulation
	print "\nPhilo Sim"
	print "-----------------------"

	# Sim Constants
	n = 1000000
	dt = 0.001

	# Flight Variables
	flight_time = 0			# sec


	# Flight Sim
	# ----------------------------------------
	print("Initial Vehicle Dry Mass (kg): \t\t\t %.6f" %vehicle.dry_mass)
	print("Initial Fuel Mass (kg): \t\t\t %.6f" %vehicle.fuel_mass)
	print("Initial Vehicle Wet Mass (kg): \t\t\t %.6f" %vehicle.wet_mass)
	print("Exhaust Mass Flow (kg/s): \t\t\t %.6f" %vehicle.mass_flow)

	# Using Rocket Equation
	delta_v = vehicle.engine.V_e * np.log(vehicle.wet_mass/vehicle.dry_mass)
	print("Delta V (m/s): \t\t\t\t\t %.6f" %delta_v)

	# Using Mass Flow
	flight_time = vehicle.fuel_mass/vehicle.mass_flow
	print("Constant Thrust - Flight Time (sec): \t\t %.6f" %flight_time)

	flight_time = 0

	# Using Numerical Approx, mass loss thrust compensation
	# 	This function compensates for the change in thrust due to
	#	mass loss during flight. More fuel you use, the less thrust 
	#	you need to null-out m*g.
	while (vehicle.fuel_mass > 0):
		vehicle.veh_mass = vehicle.dry_mass + vehicle.fuel_mass	
		vehicle.Fnull = vehicle.veh_mass*g
		vehicle.mass_flow = vehicle.Fnull/vehicle.engine.calc_Ve()
		vehicle.fuel_mass -= vehicle.mass_flow*dt
		flight_time += dt 
		
	print("Constant Acceleration - Flight Time (sec): \t %.6f" %flight_time)
	print "-----------------------\n"
	# ----------------------------------------

	#x = np.zeros ( (n,3) )

	# Plot Data
	#plt.figure()
	#plt.plot(x[:,0])
	#plt.show()

def load_config(cfgfile):
	cfg = None
	tanks = None
	fuels = None
	heaters = None

	with open(cfgfile) as cfgson:
		cfg = json.load(cfgson)

	with open("tanks.json") as tankson:
		tanks = json.load(tankson)

	with open("fuels.json") as fuelson:
		fuels = json.load(fuelson)

	with open("heaters.json") as heaterson:
		heaters = json.load(heaterson)

	cfgdat = {
				"tank": None,
				"avionics_mass": None,
				"mech_mass": None,
				"P_ambient": None,
				"P_in": None,
				"heater": None,
				"fuel": None
	}

	# get a list of the sections in the config
	sections = [section for section in cfg]
	
	# parse the config section by section and load values
	# into cfgdat
	if "Vehicle" in sections:
		sec = cfg["Vehicle"]

		if "tank" in sec:
			cfgdat["tank"] = tanks[sec["tank"]]
		if "avionics_mass" in sec:
			cfgdat["avionics_mass"] = sec["avionics_mass"]
		if "mech_mass" in sec:
			cfgdat["mech_mass"] = sec["mech_mass"]
	
	if "Engine" in sections:
		sec = cfg["Engine"]

		if "fuel" in sec:
			cfgdat["fuel"] = fuels[sec["fuel"]]
		if "P_ambient" in sec:
			cfgdat["P_ambient"] = sec["P_ambient"]
		if "P_in" in sec:
			cfgdat["P_in"] = sec["P_in"]
		if "heater" in sec:
			cfgdat["heater"] = heaters[sec["heater"]]

	# Initialize a Tank object
	tankdat = cfgdat["tank"]
	tankobj = Tank(tankdat["volume"], tankdat["pressure"], tankdat["tank_mass"], tankdat["reg_min"], tankdat["reg_max"], tankdat["temp"])
	
	# Initialize a Fuel Object
	fueldat = cfgdat["fuel"]
	fuelobj = Fuel(fueldat["fuel_type"], fueldat["cp"], fueldat["cv"], fueldat["molar_mass"])

	# Initialize a Heater Object
	heaterdat = cfgdat["heater"] 
	heaterobj = Heater(heaterdat["T_chamber"])

	# Initialize an Engine Object
	engineobj = Engine(fuelobj, cfgdat["P_in"], cfgdat["P_ambient"], heaterobj)

	# Create the vehicle object
	vehicleobj = Vehicle(cfgdat["avionics_mass"], cfgdat["mech_mass"], tankobj, engineobj, fuelobj)

	return vehicleobj

if __name__ == "__main__":
	if len(sys.argv) > 1:
		if(os.path.isfile(sys.argv[1])):
			philo_cfg_file = sys.argv[1]
			vehicle = load_config(sys.argv[1])
		else:
			print "\n\033[91m{}\033[00m".format("ERROR: "),
			print "Config file not found."
			
			print "\033[93m{}\033[00m".format("WARNING: "),
			print "Loading default config: %s" % philo_cfg_file 
	else:	
		print "\n\033[93m{}\033[00m".format("WARNING:"),
		print " Config file undefined... loading default config: %s" % philo_cfg_file 
	
	vehicle = load_config(philo_cfg_file)
	run_sim(vehicle)



