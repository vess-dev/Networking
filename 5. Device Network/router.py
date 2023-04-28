#==================================================================================================================================
# router.py - Copyright Vess 2023
# This router sets up a number of devices with cartesian coordinates. They communicate with each other through the router.
#==================================================================================================================================
# Known Bugs, Issues, and Limitations
# 1. We assume each router only supports up to 1000 devices.
#==================================================================================================================================

# Imports.
import device
import os
import random
import router
import signal
import sys
import tool
import time

#==================================================================================================================================

# Port constants.
PORT_START_ROUTER = 5000

# Path constants.
PATH_ROUTERS = "./routers.txt"
PATH_ERRORS = "./errors.txt"
PATH_LOGS_DEVICES = "./logs-devices/"
PATH_LOGS_ROUTERS = "./logs-routers/"

# Packet size.
PACKET_SIZE = 4096

#==================================================================================================================================

# Load and parses the routers in the routers file.
# Pre: Takes none.
# Post: Returns a parsed list of routers.
def load_router():
	# Read in our router file data.
	handle_router = open(PATH_ROUTERS, "r")
	router_raw = handle_router.read()
	handle_router .close()
	if router_raw == "":
		return []
	# Process and split it twice.
	router_split = router_raw.split("\n")
	router_final = [temp_line.split(",") for temp_line in router_split]
	return router_final

#==================================================================================================================================

# Find an unclaimed router ID from the routers list.
# Pre: Takes the list of routers.
# Post: Returns a unique router ID.
def unique_router(input_list):
	router_list = [temp_item[0] for temp_item in input_list]
	router_id = 1
	# Count up until this ID doesn't exist in the router list.
	while "R" + str(router_id) in router_list:
		router_id += 1
	return "R" + str(router_id)

#==================================================================================================================================

# Find an unclaimed router port from the routers list.
# Pre: Takes the list of routers.
# Post: Returns a unique router port.
def unique_port(input_list):
	router_list = [temp_item[2] for temp_item in input_list]
	router_port = 0
	# Count up until this port doesn't exist in the router list.
	while str(PORT_START_ROUTER + router_port) in router_list:
		router_port += 1000
	return PORT_START_ROUTER + router_port

#==================================================================================================================================

# Remove our router from the routers file list.
# Pre: Takes a router ID.
# Post: Returns none.
def toggle_router(input_id, input_port=PORT_START_ROUTER):
	router_list = router.load_router()
	router_final = ""
	# If the router list is empty, simply add ourself.
	if len(router_list) == 0:
		router_ip = tool.get_ip()
		router_final = input_id + "," + router_ip + "," + str(PORT_START_ROUTER)
	elif len(router_list) != 0:
		# Otherwise, remove ourself from the list.
		router_clean = [temp_router for temp_router in router_list if temp_router[0] != input_id]
		# If we weren't in the list, add ourself to the list.
		if len(router_clean) == len(router_list):
			router_strings = [",".join(temp_router) for temp_router in router_clean]
			router_ip = tool.get_ip()
			router_strings.append(input_id + "," + router_ip + "," + str(input_port))
			router_final = "\n".join(router_strings)
		# If we were in the list, carry on with the new clean list.
		elif len(router_clean) != len(router_list):
			router_strings = [",".join(temp_router) for temp_router in router_clean]
			router_final = "\n".join(router_strings)
	# Write out the new toggled list of routers.
	handle_router = open(PATH_ROUTERS, "w")
	handle_router.write(router_final)
	handle_router.close()
	return

#==================================================================================================================================

# Start the router and have it generate and made a number of devices.
# Pre: Takes a (router ID, router IP, router port), device count, broadcast strength, and (grid format).
# Post: Returns none.
def init_router(input_self, input_count, input_dist, input_grid):
	# Create a list of our device's ports.
	device_list = {}
	# Iterate through and create each device.
	for temp_device in range(input_count):
		# Create a specific device ID and port.
		device_number = temp_device + 1
		device_id = input_self[0] + "D" + str(device_number)
		device_port = int(input_self[2]) + device_number
		device_list[device_id] = device_port
		# Generate random x and y coordinates for each device.
		device_x = random.randint(input_grid[0], input_grid[1])
		device_y = random.randint(input_grid[2], input_grid[3])
		device_coord = (device_x, device_y)
		tool.log_print(input_self[0], "Creating device " + device_id + " at " + str(device_coord))
		# Fork the device off and initialize it.
		handle_pid = os.fork()
		if handle_pid == 0:
			time.sleep(1)
			device.init_device(input_self, (device_id, input_self[1], device_port), device_coord, input_dist)
	# Setup the master router socket.
	socket_addr = (input_self[1], input_self[2])
	host_socket = tool.make_socket(input_self[0], socket_addr)
	while True:
		try:
			# Wait for and get data from new connections.
			client_connection, client_address = host_socket.accept()
			client_string = client_connection.recv(router.PACKET_SIZE).decode()
			# Routers make sure other routers know when routers message them.
			flag_broadcast = False
			if client_string[0] == "*":
				flag_broadcast = True
				client_string = client_string[1:]
			client_data = eval(client_string)
			tool.log_print(input_self[0], "Recieved data: " + client_string)
			# This message is for one device.
			if client_data[3] in device_list:
				target_addr = (input_self[1], device_list[client_data[3]])
				tool.send_data(target_addr, client_string)
				flag_broadcast = False
			else:
				for temp_device in device_list.keys():
					# A device can't message itself.
					if device_list[temp_device] != client_data[0]:
						target_addr = (input_self[1], device_list[temp_device])
						tool.send_data(target_addr, client_string)
				# Broadcast to all routers.
				if not flag_broadcast:
					router_list = router.load_router()
					for temp_router in router_list:
						if temp_router[0] != input_self[0]:
							target_addr = (temp_router[1], temp_router[2])
							tool.send_data(target_addr, "*" + client_string)
		except:
			pass
	return

#==================================================================================================================================

# Because Shende doesn't like early quits... They are now early returns?
# Pre: Takes a collection of command line arguments.
# Post: Returns success.
def eval_argv(input_argv):
	# Device count, broadcast strength, grid format.
	if len(input_argv) != 4:
		tool.log_print(0, "Please provide three command line variables")
		return False
	# Make sure we've recieved a positive number for devices.
	device_count = 50
	try:
		device_count = int(input_argv[1])
	except:
		tool.log_print(0, "Please provide a number for devices")
		return False
	if not (device_count >= 1):
		tool.log_print(0, "Please provide a positive number for devices")
		return False
	# Make sure we've recieved a positive number for strength.
	device_dist = 10
	try:
		device_dist = int(input_argv[2])
	except:
		tool.log_print(0, "Please provide a number for strength")
		return False
	if not (device_dist >= 1):
		tool.log_print(0, "Please provide a positive number for strength")
		return False
	# Grid format is startx,maxx,starty,maxy.
	grid_format = [0,100,0,100]
	try:
		grid_format = list(map(int, input_argv[3].split(",")))
	except:
		tool.log_print(0, "Please format the grid as startx,starty,maxx,maxy")
		return False
	if any(temp_check < 0 for temp_check in grid_format):
		tool.log_print(0, "No grid format may be less than 0")
		return False
	return (device_count, device_dist, grid_format)

#==================================================================================================================================

# If our program is being run directly, it is the main file.
if __name__ == "__main__":
	# Evaluate our command line arguments.
	router_eval = router.eval_argv(sys.argv)
	if router_eval:
		# Get a unique ID and port for the router, then get our host machine's IP.
		router_list = router.load_router()
		router_id = router.unique_router(router_list)
		router_port = router.unique_port(router_list)
		router_ip = tool.get_ip()
		# Toggle the router in the list of routers.
		router.toggle_router(router_id, router_port)
		tool.log_print(router_id, "Starting..")
		tool.log_print(router_id, str(router_list))
		# Catch ctrl-c on the keyboard for graceful exit.
		# Pre: Takes a signal and frame.
		# Post: Returns none.
		def signal_handler(signal, frame):
	  		tool.log_print(router_id, "Closing down..")
	  		router.toggle_router(router_id)
	  		quit()
	  	# Make sure we grab interrupt signals and handle them gracefully.
		signal.signal(signal.SIGINT, signal_handler)
		# Start the router if all goes well.
		router.init_router((router_id, router_ip, router_port), router_eval[0], router_eval[1], router_eval[2])

#==================================================================================================================================