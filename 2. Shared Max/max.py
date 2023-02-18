#==================================================================================================================================
# max.py - Copyright Vess 2023
# Proof of concept for a shared memory max sort client. Each child finds the max of a smaller set of numbers.
#==================================================================================================================================
# Known Bugs, Issues, and Limitations
# 1. All numbers must currently be less than 255.
# 2. No error checking on the input array.
#==================================================================================================================================

# Imports.
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

# Return a debug array for testing.
def array_debug(num_count):
	array_random = []
	for temp_itr in range(num_count):
		array_random.append(random.randint(0, 255))
	return array_random

#==================================================================================================================================

def array_split(input_list, array_count):
	return [input_list[temp_itr::array_count] for temp_itr in range(array_count)]

#==================================================================================================================================

# Get the array of numbers.
def array_get(flag_debug):
	if flag_debug:
		array_size = random.randint(0, 100)
		return array_debug(array_size)
	print("Please define an array of numbers in the format of: 1, 2, 3")
	input_user = input("> ")
	input_clean = input_user.replace(" ", "").split(",")
	input_nums = list(
		map(int, input_clean)
	)
	if any(temp_x > 255 for temp_x in input_nums):
		print("Error: No number can be greater than 255.")
		exit()
	return input_nums

#==================================================================================================================================

# Get the max of an array of numbers.
def max_get(input_nums):
	sys.exit(max(input_nums))

#==================================================================================================================================

# Setup the parent process.
def parent_setup(child_count, input_nums):
	proc_pids = []
	for temp_window in array_split(input_nums, child_count):
		proc_pid = os.fork()
		if proc_pid == 0:
			max_get(temp_window)
		else:
			proc_pids.append(proc_pid)
	print("Process pids: " + str(proc_pids))
	proc_results = []
	while proc_pids:
		proc_pid, proc_code = os.wait()
		if proc_pid == 0:
			time.sleep(1)
		else:
			proc_results.append(proc_code//256)
			proc_pids.remove(proc_pid)
	return max(proc_results)

#==================================================================================================================================

if __name__ == "__main__":
	child_count = 1
	if len(sys.argv) > 1:
		try:
			int(sys.argv[1])
		except:
			print("Error: Child count is not a number.")
			exit()
		if int(sys.argv[1]) < 0:
			print("Error: Child count cannot be less than 0.")
			exit()
		child_count = int(sys.argv[1])
	input_nums = array_get(False)
	if child_count > len(input_nums):
		print("Error: More chilren than numbers in list.")
		exit()
	random.shuffle(input_nums)
	print("Shuffled array of numbers: " + str(input_nums))
	array_max = parent_setup(child_count, input_nums)
	print("The max of the array is: " + str(array_max))
	exit()
	
#==================================================================================================================================