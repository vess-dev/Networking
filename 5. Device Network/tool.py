#==================================================================================================================================
# tool.py - Copyright Vess 2023
# This file contains shared misc functions between the router and the devices.
#==================================================================================================================================

# Imports.
import os
import router
import shutil
import socket
import tool

#==================================================================================================================================

# Get the IP of the machine.
# Pre: Takes none.
# Post: Returns the current IP of the machine, or False.
def get_ip():
	# Setup a quick broadcast and grab the machine's IP.
	host_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	host_ip = False
	try:
		host_socket.connect(("192.255.255.255", 1))
		host_ip = host_socket.getsockname()[0]
	finally:
		host_socket.close()
	return host_ip

#==================================================================================================================================

# Open a connection to an IP.
# Pre: Takes the target IP and target port.
# Post: Returns the socket handle.
def make_socket(input_id, input_addr):
	host_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	host_address = (input_addr[0], input_addr[1])
	tool.log_print(input_id, "Socket is listening on port: " + str(input_addr[1]))
	host_socket.bind(host_address)
	host_socket.listen(1000)
	host_socket.setblocking(0)
	return host_socket

#==================================================================================================================================

# Sends data to a target IP.
# Pre: Takes a target ip, port, and some data to send.
# Post: Returns none.
def send_data(input_addr, input_data):
	host_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	host_address = (input_addr[0], int(input_addr[1]))
	host_socket.connect(host_address)
	host_socket.send(input_data.encode())
	host_socket.close()
	return

#==================================================================================================================================

# Formatting for output messages.
# Pre: Takes an ID, and a string to output.
# Post: Returns none.
def log_print(input_id, input_string):
	# 0 is a reserved ID for errors.
	if input_id == 0:
		# Open the error file and log the error.
		string_out = "ERROR: " + input_string + ".\n"
		print(string_out, end="")
		handle_error = open(router.PATH_ERRORS, "a")
		handle_error.write(string_out)
		handle_error.close()
		return	
	else:
		# Open the respecting router or device log file and log the output.
		string_out = input_id + ": " + input_string + ".\n"
		print(string_out, end="")
		log_path = ""
		if "D" not in input_id:
			log_path = router.PATH_LOGS_ROUTERS + input_id + ".txt"
		elif "D" in input_id:
			log_path = router.PATH_LOGS_DEVICES + input_id + ".txt"
		handle_log = open(log_path, "a")
		handle_log.write(string_out)
		handle_log.close()
	return

#==================================================================================================================================

# Wipes a folder. Misc function for clearing logs.
# Pre: Takes a folder path.
# Post: Returns none.
def clear_folder(input_path):
	# Walk the input folder and wipe it clean.
	for temp_file in os.listdir(input_path):
		file_path = os.path.join(input_path, temp_file)
		# If they are files-
		if os.path.isfile(file_path) or os.path.islink(file_path):
			os.unlink(file_path)
		# If they are folders-
		elif os.path.isdir(file_path):
			shutil.rmtree(file_path)
	return

#==================================================================================================================================

# If our program is being run directly, it is the main file.
if __name__ == "__main__":
	# If tool is run as main, clear logs.
	tool.clear_folder(router.PATH_LOGS_DEVICES)
	tool.clear_folder(router.PATH_LOGS_ROUTERS)
	quit()

#==================================================================================================================================