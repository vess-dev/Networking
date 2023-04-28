#==================================================================================================================================
# device.py - Copyright Vess 2023
# This device recieves cartesian coordinates, and attempts to reach and path to other devices in the network through the router.
#==================================================================================================================================
# Known Bugs, Issues, and Limitations
# 1. We generally assume that each device will have the same broadcast strength.
#==================================================================================================================================

# Imports.
import copy
import math
import pprint
import router
import signal
import sys
import time
import tool

#==================================================================================================================================

# Check if another coordinate is within range.
# Pre: Takes a current (x, y) and a target (x, y) set of coordinates.
# Post: Returns success.
def check_dist(input_current, input_target, input_dist):
	distance_value = math.sqrt(((input_target[0] - input_current[0])**2) + ((input_target[1] - input_current[1])**2))
	if distance_value < input_dist:
		return True
	return False

#==================================================================================================================================

# Start the device and have it generate a routing table by trying to contact other devices.
# Pre: Takes a (router ID, router IP, router port), (device ID, device IP, device port), (x, y), hearing distance.
# Post: Returns none.
def init_device(input_parent, input_self, input_coord, input_dist):
	# Catch ctrl-c on the keyboard for graceful exit.
	# Pre: Takes a signal and frame.
	# Post: Returns none.
	def signal_handler(signal, frame):
  		tool.log_print(input_self[0], "Closing down..")
  		sys.exit()
  	# Reset the signal handler for the forked process.
	signal.signal(signal.SIGINT, signal_handler)
	tool.log_print(input_self[0], "Device alive at " + str(input_coord))
	device_table = {}
	# Setup the device socket.
	socket_addr = (input_self[1], input_self[2])
	host_socket = tool.make_socket(input_self[0], socket_addr)
	# Give time for each device to setup a socket.
	time.sleep(1)
	device_first = True
	while True:
		# Send out an initial broadcast ping.
		if device_first:
			# Our data packet format is:
			# [0] Sender ID, [1] sender coord, [2] sender strength, [3] next hop ID, [4] target ID, [5] sender table, [6] hop count.
			parent_addr = (input_parent[1], input_parent[2])
			packet_data = (input_self[0], input_coord, input_dist, "", "", device_table, 1)
			tool.send_data(parent_addr, str(packet_data))
			device_first = False
		try:
			# Wait for and get data from new connections.
			client_connection, client_address = host_socket.accept()
			client_string = client_connection.recv(router.PACKET_SIZE).decode()
			client_data = eval(client_string)
			# Ignore all devices too far away.
			if check_dist(input_coord, client_data[1], client_data[2]):
				if (input_self[0] == client_data[4]) or (not client_data[3]):
					tool.log_print(input_self[0], "Recieved data: " + client_string)
					device_old = copy.deepcopy(device_table)
					# We've never seen the sender device...
					if not client_data[0] in device_table:
						tool.log_print(input_self[0], "Found a new device: " + client_data[0])
						device_table[client_data[0]] = [client_data[0], client_data[6]]
					# Add their table to ours.
					for temp_device in client_data[5].keys():
						# Don't add ourself.
						if temp_device != input_self[0]:
							if not temp_device in device_table:
								tool.log_print(input_self[0], "Found a new device: " + temp_device + ", from: " + client_data[0])
								device_table[temp_device] = [client_data[0], client_data[5][temp_device][1] + client_data[6]]
								# Let the new device know we exist.
								parent_addr = (input_parent[1], input_parent[2])
								packet_data = (input_self[0], input_coord, input_dist, client_data[0], temp_device, device_table, 1)
								tool.send_data(parent_addr, str(packet_data))
							elif client_data[5][temp_device][1] + client_data[6] < device_table[temp_device][1]:
								tool.log_print(input_self[0], "Found a better path for: " + temp_device + ", from " + client_data[0] + ", instead of " + device_table[temp_device][0] + ", in " + str(client_data[5][temp_device][1] + client_data[6]) + " hops, over " + str(device_table[temp_device][1]) + " hops.")
								device_table[temp_device] = [client_data[0], client_data[5][temp_device][1] + client_data[6]]
					# Send out table updates.
					if device_table != device_old:
						string_format = pprint.PrettyPrinter(indent=4, width=30)
						string_table = string_format.pformat(device_table)
						tool.log_print(input_self[0], "New table: \n" + string_table)
						if len(device_table) != 1:
							for temp_target in device_table.keys():
								parent_addr = (input_parent[1], input_parent[2])
								packet_data = (input_self[0], input_coord, input_dist, device_table[temp_target][0], temp_target, device_table, 1)
								tool.send_data(parent_addr, str(packet_data))
				# We are the hop.
				elif input_self[0] == client_data[3]:
					tool.log_print(input_self[0], "Recieved data: " + client_string)
					parent_addr = (input_parent[1], input_parent[2])
					packet_data = (input_self[0], input_coord, input_dist, device_table[client_data[4]][0], client_data[4], client_data[5], client_data[6] + 1)
					tool.send_data(parent_addr, str(packet_data))
					tool.log_print(input_self[0], "Passed data from: " + client_data[0] + ", to " + device_table[client_data[4]][0] + ", for " + client_data[4])
		except:
			pass

#==================================================================================================================================