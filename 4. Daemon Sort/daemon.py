#==================================================================================================================================
# daemon.py - Copyright Vess 2023
# This daemon lists for network requests and initializes parallel daemons or runs a program at a specific port.
#==================================================================================================================================
# Known Bugs, Issues, and Limitations
# 1. Timing might be off on many parallel daemons.
#==================================================================================================================================

# Imports.
import itertools
import os
import random
import signal
import socket
import sys
import subprocess
import tool

#==================================================================================================================================

# Simply grabs the list of nodes and removes the host node, then shuffles them.
# Pre: Takes none.
# Post: Returns a shuffled list of nodes minus the host node.
def node_update():
	# Grab the current host ip.
	host_ip = tool.get_ip()
	if not host_ip:
		# Break if we failed to get the proper IP.
		tool.print_out("Failed to get the host IP", True)
		return False
	# Grab the available node list and remove the host, then shuffle.
	node_list = tool.get_file("nodes.txt")
	if host_ip in node_list:
		node_list.remove(host_ip)
	random.shuffle(node_list)
	tool.print_out("List of nodes: " + str(node_list))
	return node_list

#==================================================================================================================================

# Begins listening for incoming commands.
# Pre: Takes none.
# Post: Returns True if it ran fine, otherwise return False.
def init_daemon():
	# Setup and listen to the current machine's IP.
	host_ip = tool.get_ip()
	if not host_ip:
		# Break if we failed to get the proper IP.
		tool.print_out("Failed to get the host IP", True)
		return False
	tool.print_out("The host IP is " + str(host_ip))
	# Get the list of available nodes.
	node_list = node_update()
	# Bind to the host address and daemon port and listen.
	host_socket = tool.get_socket(host_ip, tool.PORT_DAEMON)
	while True:
		# Wait for and get data from new connections.
		client_connection, client_address = host_socket.accept()
		tool.print_out("Connection from: " + str(client_address))
		client_data = client_connection.recv(1024).decode().split(" ")
		tool.print_out("Received command: " + str(client_data))
		# Get the list of available nodes.
		node_list = node_update()
		if client_data[0] == "p":
			node_cycle = itertools.cycle(node_list)
			for temp_itr in range(int(client_data[1])):
				node_ip = next(node_cycle)
				# Specification by professor not clear. Agnostically run commands? But also give out IDs?
				# The IDs would mean the master dispatches dynamic ID calls: 0, 1, 2, etc, to the daemon instead of one request.
				# The only way for this to work is that the daemon must make a choice on command type.
				# Thusly, is not possible to separate the daemon completely from the hybrid.
				if "hybrid.py" in client_data:
					name_parts = client_data[-1].split(".")
					file_name =  name_parts[0] + str(temp_itr) + "." + name_parts[1]
					tool.send_data(node_ip, tool.PORT_DAEMON, "r " + " ".join(client_data[2:7]) + " " + str(temp_itr) + " " + file_name)
				else:
					# However, the daemon can still run random requested programs... If there was a client to request such.
					tool.send_data(node_ip, tool.PORT_DAEMON, "r " + " ".join(client_data[2:]))
				tool.print_out("Dispatched work to: " + node_ip)
		elif client_data[0] == "r":
			proc_pid = os.fork()
			if proc_pid == 0:
				os.system(" ".join(client_data[1::]))
				quit()
	host_socket.close()
	return True

#==================================================================================================================================

# Add or remove the daemon from the node list.
# Pre: Takes a type, either "add" or "sub".
# Post: Returns none.
def node_clean(input_type):
	# Grab the host IP.
	host_ip = tool.get_ip()
	if not host_ip:
		# Break if we failed to get the proper IP.
		tool.print_out("Failed to get the host IP", True)
		return False
	# Get the list of available nodes.
	node_list = tool.get_file("nodes.txt")
	# Add or remove the host IP from the node list.
	if input_type == "add":
		if host_ip not in node_list:
			node_list.append(host_ip)	
	elif input_type == "sub":
		if host_ip in node_list:
			node_list.remove(host_ip)
	# Write the updates to the nodes file.
	handle_node = open("nodes.txt", "w")
	for temp_node in node_list:
		handle_node.write(temp_node + "\n")
	handle_node.close()
	tool.print_out("Cleaned up the node list")
	return

#==================================================================================================================================

# Catch ctrl-c on the keyboard for graceful exit.
# Pre: Takes a signal and frame.
# Post: Returns none.
def signal_handler(signal, frame):
  node_clean("sub")
  tool.print_out("The daemon has closed down")
  quit()
  return

#==================================================================================================================================

if __name__ == "__main__":
	tool.print_out("The daemon has started")
	signal.signal(signal.SIGINT, signal_handler)
	node_clean("add")
	# Start the daemon if all goes well.
	result_daemon = init_daemon()
	if not result_node:
		tool.print_out("Critical error in daemon init", True)
		quit()
	node_clean("sub")
	quit()

#==================================================================================================================================