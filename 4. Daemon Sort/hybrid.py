#==================================================================================================================================
# hybrid.py - Copyright Vess 2023
# This program either runs as a master that splits files, or a slave that merges and sorts them.
#==================================================================================================================================
# Known Bugs, Issues, and Limitations
# 1. Timing might be off on larger file splits.
# 2. A master process requires at least two daemons to be running.
# 3. This entire process only essentially works on a file share.
#==================================================================================================================================

# Imports.
import time
import tool
import socket
import sys

#==================================================================================================================================

# Splits a list into equally distributed chunks.
# Pre: Takes a list, and a chunk count.
# Post: Returns a list of split lists.
def split_array(input_list, input_chunks):
	return [input_list[temp_itr::input_chunks] for temp_itr in range(input_chunks)]

#==================================================================================================================================

# Splits a file of numbers into equally distributed files of numbers.
# Pre: Takes a target file and a number of chunks to split it into.
# Post: Returns none.
def split_file(input_file, input_chunks):
	# Read in and parse the input data.
	num_data = tool.get_file(input_file)
	num_data = list(map(int, num_data))
	tool.print_out("Got input data: " + str(num_data))
	# Split out the input data into chunks.
	num_lists = split_array(num_data, input_chunks)
	tool.print_out("Split input data: " + str(num_lists))
	for temp_itr in range(input_chunks):
		handle_name = "input" + str(temp_itr) + ".txt"
		write_file(handle_name, num_lists[temp_itr])
	return

#==================================================================================================================================

# Writes some numbers to a target file.
# Pre: Takes a target file and some number data.
# Post: Returns none.
def write_file(input_file, input_data):
	handle_file = open(input_file, "w")
	for temp_num in input_data:
		handle_file.write(str(temp_num) + "\n")
	handle_file.close()
	tool.print_out("Wrote data to: " + input_file)
	return

#==================================================================================================================================

# Splits a file and requests slaves from the daemon.
# Pre: Takes in the number of children.
# Post: Returns True if it ran fine, otherwise return False.
def init_master(input_children):
	# Write those chunks to files.
	# The "split" command is not system agnostic.
	split_file("input.txt", input_children)
	# Dispatch for the daemon to start workers.
	host_ip = tool.get_ip()
	tool.send_data(host_ip, tool.PORT_DAEMON, "p " + str(input_children) + " python hybrid.py s " + host_ip + " " + str(tool.PORT_MASTER) + " input.txt")
	tool.print_out("Dispatched for work to daemon")
	# Begin listening for worker reports.
	host_ip = tool.get_ip()
	if not host_ip:
		# Break if we failed to get the proper IP.
		tool.print_out("Failed to get the host IP", True)
		return False
	tool.print_out("The host IP is " + str(host_ip))
	host_socket = tool.get_socket(host_ip, tool.PORT_MASTER)
	# Keep track of the finished slaves.
	slave_finish = []
	while True:
		# Wait for and get data from new connections.
		client_connection, client_address = host_socket.accept()
		tool.print_out("Connection from: " + str(client_address))
		slave_finish.append(client_connection)
		client_data = client_connection.recv(1024)
		tool.print_out("Received finish from slave: " + client_data.decode())
		if len(slave_finish) == input_children:
			for temp_slave in slave_finish:
				temp_slave.sendall(bytes("f", "UTF-8"))
			break
	# Load in all files and merge them.
	chunk_all = []
	for temp_itr in range(input_children):
		file_name = "input" + str(temp_itr) + ".txt"
		num_data = tool.get_file(file_name)
		num_data = list(map(int, num_data))
		tool.print_out("Got chunk data: " + str(num_data))
		chunk_all.extend(num_data)
	# Sort the final array and write to an output file.
	chunk_all.sort()
	write_file("output.txt", chunk_all)
	return True

#==================================================================================================================================

# Splits a file and requests slaves from the daemon.
# Pre: Takes in the master IP and port, the slave ID, and the target file.
# Post: Returns none.
def init_slave(input_ip, input_port, input_id, input_file):
	# Reads in the file's numbers, sorts them, and writes them back.
	num_data = tool.get_file(input_file)
	num_data = list(map(int, num_data))
	num_data.sort()
	write_file(input_file, num_data)
	tool.print_out("Slave " + str(input_id) + " wrote file: " + input_file)
	# Lets the master know it has finished.
	tool.send_data(input_ip, input_port, str(input_id), True)
	tool.print_out("Slave " + str(input_id) + " dying now...")
	quit()
	return

#==================================================================================================================================

if __name__ == "__main__":
	# Parse the given command line arguments.
	tool.print_out("Got system arguments: " + str(sys.argv))
	# Some additional fault tolerance.
	if len(sys.argv) <= 1:
		tool.print_out("There was no master or slave argument given", True)
		quit()
	# Now we split out into either a master or slave.
	if "m" in sys.argv[1]:
		if len(sys.argv) != 3:
			tool.print_out("Master mode takes three arguments only", True)
			quit()
		# Check and see if the child count is malformed.
		child_count = 1
		try:
			child_count = int(sys.argv[2])
			if (child_count < 1):
				raise Exception("Test")
		except:
			tool.print_out("Malformed argument for number of children", True)
			quit()
		# Start the master process and check for faults.
		tool.print_out("Starting a master process")
		result_master = init_master(child_count)
		if not result_master:
			tool.print_out("Critical error in master init", True)
			quit()
		tool.print_out("The master has closed down")
	elif "s" in sys.argv[1]:
		if len(sys.argv) != 6:
			tool.print_out("Slave mode takes five arguments only", True)
			quit()
		# Check and see if the master port is malformed.
		master_port = tool.PORT_MASTER
		slave_id = 0
		target_file = ""
		try:
			master_port = int(sys.argv[3])
			slave_id = int(sys.argv[4])
			target_file = sys.argv[5]
			open(target_file, "r")
		except:
			tool.print_out("Malformed arguments for master port, ID, or target file.", True)
			quit()
		# Start the slave process.
		tool.print_out("Starting a slave process")
		init_slave(sys.argv[2], master_port, slave_id, target_file)
	else:
		tool.print_out("Malformed argument for mode", True)
		quit()
	quit()

#==================================================================================================================================