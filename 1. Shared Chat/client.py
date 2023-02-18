#==================================================================================================================================
# client.py - Copyright Vess 2023
# Proof of concept for a shared memory chat client in Python. Uses a simple read / write flag to check for messages.
#==================================================================================================================================
# Known Bugs, Issues, and Limitations
# 1. If client 1 joins and sends a message, the "connect message" will be lost.
# 2. A client has to send an empty message to recieve updates. Due to timing, messages can be lost.
# 3. There is no message queue for either user, which sort of leads to the two aforementioned issues. It is trivial to implement.
#==================================================================================================================================

# Imports.
import os
import sys
from multiprocessing import shared_memory

#==================================================================================================================================

# Clear the termainl output.
def client_clear():
	os.system("cls" if os.name == "nt" else "clear")
	return

#==================================================================================================================================

# Debug function for viewing the shared memory.
def client_debug():
	print(bytes(mem_share.buf))
	return

#==================================================================================================================================

# Setup the shared memory block.
def mem_setup(mem_size):
	client_num = 1
	# Try to create a shared memory block. If it already exists, just connect to it.
	try:
		mem_share = shared_memory.SharedMemory(name="chat", create=True, size=mem_size)
		print("You are client 1.")
		client_num = 1
		client_offset = 0
		client_mid = (mem_size//2)
		client_max = mem_size
	except:
		mem_share = shared_memory.SharedMemory(name="chat", create=False, size=mem_size)
		print("You are client 2.")
		client_num = 2
		client_offset = (mem_size//2)
		client_mid = 0
		client_max = client_offset
	return mem_share, [client_num, client_offset, client_mid, client_max]

#==================================================================================================================================

# Check if the read flag is on. If so, unset it and print the message.
def mem_read(mem_share, client_num, client_mid, client_max):
	# Invert the client number.
	client_other = str(1+(client_num%2))
	# Read a message only if the flag is set.
	if mem_share.buf[client_mid:client_mid+1] == bytes("*", "utf-8"):
		mem_message = str(bytes(mem_share.buf[client_mid+1:client_max]).decode()).split("#")[0]
		print("Client " + client_other + ": " + mem_message)
		mem_share.buf[client_mid:client_mid+1] = bytes(" ", "utf-8")
	return

# Set the read flag to on, and write a message to the memory.
def mem_write(mem_share, client_offset, mem_message):
	mem_share.buf[client_offset:client_offset+1] = bytes("*", "utf-8")
	mem_padding = len(mem_message)
	mem_share.buf[client_offset+1:client_offset+len(mem_message)+2] = bytes(mem_message + "#", "utf-8")
	return

#==================================================================================================================================

# Setup the client and begin to listen to the shared memory block.
def client_setup(mem_share, mem_size, client_data):
	client_num, client_offset, client_mid, client_max = client_data
	client_clear()
	user_input = ""
	mem_write(mem_share, client_offset, "[Has connected.]")
	mem_read(mem_share, client_num, client_mid, client_max)
	# / will be considered a special character that by itself ends the program.
	while True:
		user_input = input("Client " + str(client_num) + ": ")
		# Check the message length.
		if (len(user_input)+2) >= (mem_size//2):
			print("Error: That message is too long and won't be sent.")
		# Check for a reserved character.
		if "#" in user_input:
			print("Error: # is a reserved character.")
		# Check for the end character.
		if user_input == "/":
			mem_write(mem_share, client_offset, "[Has disconnected.]")
			return
		# Check if empty input.
		if user_input != "":
			mem_write(mem_share, client_offset, user_input)
		mem_read(mem_share, client_num, client_mid, client_max)
	return

#==================================================================================================================================

if __name__ == "__main__":
	# Get the total size of shared memory as a CLI argument.
	mem_size = 100
	if len(sys.argv) > 1:
		try:
			int(sys.argv[1])
		except:
			print("Error: Mem size is not a number.")
			exit()
		if int(sys.argv[1]) <= 4:
			print("Error: Mem size cannot be less than 4.")
			exit()
		if int(sys.argv[1])%2 != 0:
			print("Error: Mem size is not divisable by 2.")
			exit()
		mem_size = int(sys.argv[1])
	# Get a handle for a shared memory block, and the client type.
	mem_share, client_data = mem_setup(mem_size)
	# Start the client.
	client_setup(mem_share, mem_size, client_data)
	# Make sure to clean up the shared memory space.
	mem_share.close()
	mem_share.unlink()
	exit()

#==================================================================================================================================
