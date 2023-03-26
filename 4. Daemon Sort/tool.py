#==================================================================================================================================
# tool.py - Copyright Vess 2023
# This file contains shared misc functions between the daemon and the hybrid.
#==================================================================================================================================

# Imports.
import os
import random
import socket

#==================================================================================================================================

# Constants.
PORT_DAEMON = 5000
PORT_MASTER = PORT_DAEMON+1

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

# Open a file and parse the data inside.
# Pre: Takes the files name.
# Post: Returns the file's parsed content.
def get_file(input_file):
	# Read the file and cast to a list, splitting by newline.
	handle_file = open(input_file, "r")
	file_data = handle_file.read()
	handle_file.close()
	file_data = file_data.split("\n")
	if "" in file_data:
		file_data.remove("")
	return file_data

#==================================================================================================================================

# Open a connection to an IP.
# Pre: Takes the target IP and target port.
# Post: Returns the socket handle.
def get_socket(input_ip, input_port):
	host_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	host_address = (input_ip, input_port)
	print_out("Socket is listening to IP: " + str(host_address[0]))
	print_out("Socket is listening on port: " + str(host_address[1]))
	host_socket.bind(host_address)
	host_socket.listen(1)
	return host_socket

#==================================================================================================================================

# Sends data to a target IP.
# Pre: Takes a target ip, port, and some data to send.
# Post: Returns none.
def send_data(input_ip, input_port, input_data, input_listen=False):
	host_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	host_address = (input_ip, input_port)
	host_socket.connect(host_address)
	host_socket.sendall(bytes(input_data, "UTF-8"))
	if input_listen:
		print_out("Notified master of finish")
		print_out("Waiting for death..")
		host_data = host_socket.recv(1024).decode()
	host_socket.close()
	return

#==================================================================================================================================

# Formatting for output messages.
# Pre: Takes a string to output.
# Post: Returns none.
def print_out(input_string, input_error=False):
	if not input_error:
		print("Debug: " + input_string + ".")
	else:
		print("ERROR: " + input_string + ".")
	return

#==================================================================================================================================

# Creates an example input file.
# Pre: Takes none.
# Post: Returns none.
def init_input():
	handle_input = open("input.txt", "w")
	# Generate and shuffle numbers 1-100.
	input_data = list(range(1, 101))
	random.shuffle(input_data)
	# Write the shuffled numbers to the file.
	for temp_int in input_data:
		packet_data = str(temp_int) + "\n"
		handle_input.write(packet_data)
	handle_input.close()
	return

#==================================================================================================================================

if __name__ == "__main__":
	init_input()
	quit()

#==================================================================================================================================