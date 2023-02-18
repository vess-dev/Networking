#==================================================================================================================================
# sort.py - Copyright Vess 2023
# Proof of concept for a shared memory mergesort client. Child processes sort and merge chunks.
#==================================================================================================================================
# Known Bugs, Issues, and Limitations
# 1. There is a max of 251 child processes due to how flag codes work.
# 2. An incredibly small race condition with dispatches from the server is theoretically possible?
#==================================================================================================================================

# Imports.
import math
from multiprocessing import shared_memory
import os
import random
import sys
import time

#==================================================================================================================================

# Clear the terminal output.
def client_clear():
	os.system("cls" if os.name == "nt" else "clear")
	return

#==================================================================================================================================

# Debug function to create a input file of random numbers.
def file_debug(file_name, num_min, num_max, num_range):
	file_handle = open(file_name, "w")
	for temp_itr in range(random.randint(num_min, num_max)):
		file_handle.write(str(random.randint(-num_range, num_range)) + " ")
	file_handle.close()
	return
	
#==================================================================================================================================

# Read and cast in an input file of numbers delimited by spaces.
def file_read(file_name):
	file_handle = open(file_name, "r")
	file_data = file_handle.read()
	file_data = file_data.split(" ")
	# Remove last space item if one exists from debug file.
	if "" in file_data:
		file_data.remove("")
	# Split by space and cast to integers.
	file_list = list(map(int, file_data))
	server_status("Read in " + str(len(file_list)) + " numbers from " + file_name)
	return file_list

#==================================================================================================================================

# Find the byte length of the number.
def byte_len(num_input):
	return math.ceil(num_input.bit_length() / 8.0)

#==================================================================================================================================

# Cast a list of integers to a list of bytes after finding the max.
def byte_cast(num_list):
	byte_list = []
	# Find the max required number of bytes.
	byte_size = 0
	for temp_num in num_list:
		byte_count = byte_len(temp_num)
		if byte_count > byte_size:
			byte_size= byte_count
	# Convert the numbers to signed big endian bytes.
	for temp_num in num_list:
		byte_new = temp_num.to_bytes(byte_size, "big", signed=True)
		byte_list.append(byte_new)
	return byte_list, byte_size

#==================================================================================================================================

# Cast a single list of bytes to an integer.
def num_cast(byte_list):
	return int.from_bytes(byte_list, "big", signed=True)

#==================================================================================================================================

# Simply return the memory flag buffer as a list string.
def flag_status(mem_flag):
	return list(mem_flag.buf)

#==================================================================================================================================

# Read memory byte data from a specific chunk number or range as integers.
def mem_read(mem_target, chunk_index, byte_size):
	# Find the appropriate start and end indexes for the chunk number.
	mem_start = chunk_index * (100 * byte_size)
	mem_end = mem_start + (100 * byte_size)
	mem_max = len(mem_target.buf)
	if mem_end > mem_max:
		mem_end = mem_max
	# Convert our chunk bytes to a list of integers.
	num_cache = []
	for temp_index in range(mem_start, mem_end, byte_size):
		num_int = num_cast(mem_target.buf[temp_index:temp_index+byte_size])
		num_cache.append(num_int)
	return num_cache

#==================================================================================================================================

# Write memory byte data to a target memory at a certain chunk number.
def mem_write(mem_target, chunk_index, chunk_data, byte_size):
	mem_start = chunk_index * (100 * byte_size)
	mem_end = mem_start + (len(chunk_data) * byte_size)
	for temp_pair in zip(range(mem_start, mem_end, byte_size), chunk_data):
		mem_target.buf[temp_pair[0]:temp_pair[0]+byte_size] = temp_pair[1]
	return

#==================================================================================================================================

def mem_dump(mem_target, byte_size):
	num_cache = []
	for temp_index in range(0, len(mem_target.buf), byte_size):
		num_int = num_cast(mem_target.buf[temp_index:temp_index+byte_size])
		num_cache.append(num_int)
	print(num_cache)
	return

#==================================================================================================================================

# Sort and return a list of numbers.
def num_sort(num_list):
	return sorted(num_list)

#==================================================================================================================================

# A simple function to clean up our server memory on exit.
def server_shutdown(mem_list):
	for temp_mem in mem_list:
		temp_mem.close()
		temp_mem.unlink()
	return

#==================================================================================================================================

# Simple consolidation of server prints.
def server_status(status_message):
	print("Server status: " + status_message + ".")
	return

#==================================================================================================================================

# Return a free child.
def child_free(mem_target, child_count):
	for temp_id in range(child_count):
		if temp_id not in mem_target.buf:
			return temp_id
	return -1

#==================================================================================================================================

# Simple consolidation of child prints.
def child_status(child_id, status_message):
	print("Child " + str(child_id) + " status: " + status_message + ".")
	return

#==================================================================================================================================

# This is where a child is started and looks for work.
def child_start(child_id, mem_share, mem_flag, mem_kill, byte_size, flag_guide):
	flag_pos = 0
	while True:
		work_list = [temp_index for temp_index, temp_check in enumerate(mem_flag.buf) if temp_check == child_id]
		if work_list:
			child_status(child_id, "Found work to do for chunks " + str(work_list))
			work_data = []
			for temp_chunk in work_list:
				work_data.extend(mem_read(mem_share, temp_chunk, byte_size))
			work_sorted = num_sort(work_data)
			work_casted, _ = byte_cast(work_sorted)
			mem_write(mem_share, work_list[0], work_casted, byte_size)
			child_status(child_id, "Sorted and merged chunks " + str(work_list))
			work_status = [flag_guide["head"]]
			if len(work_list) > 1:
				work_status.extend([flag_guide["body"]] * (len(work_list) - 1))
			mem_flag.buf[work_list[0]:work_list[-1]+1] = bytes(work_status)
		elif mem_kill.buf[0] == 1:
			sys.exit()
	return

#==================================================================================================================================

# Setup the memory sorting server which will create and dispatch children.
def server_setup(file_data, child_count):
	# Convert our file data to the least needed byte amount.
	byte_data, byte_size = byte_cast(file_data)
	# Figure out the size of our shared memory sectors.
	mem_size_share = len(byte_data) * byte_size
	mem_size_flag = math.ceil(len(byte_data) / 100)
	# Setup our shared memory for number data.
	mem_share = shared_memory.SharedMemory(name="share", create=True, size=mem_size_share)
	server_status("Shared memory setup for numbers with size " + str(mem_size_share))
	# Setup shared memory for flag statuses.
	mem_flag = shared_memory.SharedMemory(name="flag", create=True, size=mem_size_flag)
	server_status("Shared memory setup for flags with size " + str(mem_size_flag))
	# Make them all the "unsorted" flag code.
	for temp_index in range(mem_size_flag):
		mem_flag.buf[temp_index] = child_count
	# Setup shared memory for the kill flag.
	mem_kill = shared_memory.SharedMemory(name="kill", create=True, size=1)
	server_status("Shared memory setup for the kill flag")
	# Create a quick reference for flag codes.
	flag_guide = {
		"unsorted": child_count,
		"head": child_count + 1,
		"body": child_count + 2,
	}
	# Write our data to our memory.
	mem_write(mem_share, 0, byte_data, byte_size)
	server_status("Wrote numbers as bytes to shared memory")
	# Create the specified number of child processes.
	for temp_id in range(0, child_count):
		proc_pid = os.fork()
		if proc_pid == 0:
			child_start(temp_id, mem_share, mem_flag, mem_kill, byte_size, flag_guide)
		else:
			server_status("Created child with ID " + str(temp_id))
	# Start our server as our work dispatcher.
	server_start(mem_flag, mem_kill, child_count, flag_guide)
	# Output the finished sort.
	mem_dump(mem_share, byte_size)
	# Clean up the shared memory portions.
	server_shutdown([mem_share, mem_flag, mem_kill])
	return

#==================================================================================================================================

# This is where the server is started and dispatches work.
def server_start(mem_flag, mem_kill, child_count, flag_guide):
	# The server begins dispatching jobs and checking end state.
	while (mem_flag.buf[0] != flag_guide["head"]) or any(temp_check != flag_guide["body"] for temp_check in mem_flag.buf[1:]):
		# Keep track of which chunks are being worked on.
		work_tracker = []
		flag_list = list(enumerate(mem_flag.buf))
		for temp_pair in flag_list:
			# Wait for the next free child.
			child_next = -1
			while child_next == -1:
				child_next = child_free(mem_flag, child_count)
			# Skip the checking of already assigned chunks.
			if temp_pair[1] < child_count:
				continue
			# Dispatch a child to sort an unsorted chunk.
			elif temp_pair[1] == flag_guide["unsorted"] and temp_pair[0] not in work_tracker:
				mem_flag.buf[temp_pair[0]] = child_next
				work_tracker.append(temp_pair[0])
				server_status("Dispatched for child " + str(child_next) + " to sort chunk " + str(temp_pair[0]))
			# Dispatch a child to merge and sort multiple chunks.
			elif temp_pair[1] == flag_guide["head"] and temp_pair[0] not in work_tracker:
				chunk_next = temp_pair[0] + 1
				# Look for another chunk head.
				while chunk_next != len(mem_flag.buf):
					if flag_list[chunk_next][1] == flag_guide["head"]:
						break
					elif flag_list[chunk_next][1] != flag_guide["body"]:
						chunk_next = -1
						break
					chunk_next += 1
				else:
					continue
				if chunk_next == -1:
					continue
				chunk_end = chunk_next + 1
				# Look for extra body after another chunk head.
				while chunk_end != len(mem_flag.buf):
					if flag_list[chunk_end][1] != flag_guide["body"]:
						break
					chunk_end += 1
				chunk_end -= 1
				# Dispatch the work in a bulk write to edge out race conditions.
				work_status = [child_next] * ((chunk_end - temp_pair[0]) + 1)
				mem_flag.buf[temp_pair[0]:chunk_end+1] = bytes(work_status)
				work_tracker.append(temp_pair[0])
				work_tracker.append(flag_list[chunk_next][0])
				server_status("Dispatched for child " + str(child_next) + " to sort chunks " + str(list(range(temp_pair[0], chunk_end + 1))))
	# Send the signal for children to kill themselves.
	time.sleep(0.1)
	mem_kill.buf[0] = 1
	return

#==================================================================================================================================

if __name__ == "__main__":
	client_clear()
	# Generate a default input file.
	file_name = "./debug.txt"
	child_count = 10
	# Check that the file path argument is valid.
	if len(sys.argv) > 1:
		try:
			if sys.argv[1]:
				if not os.path.exists(sys.argv[1]):
					throw()
			file_name = sys.argv[1]
		except:
			print("Error: The first command line argument must be a valid file path")
			exit()
	else:
		# Create a debug file if no file name is specified.
		server_status("No input file was specified")
		server_status("Using a debug file of random numbers")
		if not os.path.exists(file_name):
			server_status("Creating a debug file of random numbers since none exists")
			file_debug(file_name, 1000, 2000, 100000)
	server_status("Set input file to " + file_name)
	# Check that the child processes argument is valid.
	if len(sys.argv) > 2:
		try:
			child_count = int(sys.argv[2])
			if child_count <= 0:
				throw()
		except:
			print("Error: The second command line arugment must be a positive Integer")
			exit()
	server_status("Set child count to " + str(child_count))
	file_handle = open(file_name, "r")
	file_data = file_read(file_name)
	server_setup(file_data, child_count)
	exit()

#==================================================================================================================================