# Networking

Various small Python projects done for a networking class.

The first three were assignments. The last two were tests.

## 1. Shared Chat

This program uses shared OS memory to send "chat" messages between two window clients.

To run: `python3 ./client.py`

![Example1](Images/Example1.png "Shared Chat Example")

## 2. Shared Max

This program uses forked processes to sort numbers and return the max.

To run: `python3 ./max.py [child count]`

![Example2](Images/Example2.png "Shared Max Example")

## 3. Shared Sort

This program uses forked processes and shared memory to sort numbers and return the sorted list.

The input file is expected to be space delimited numbers.

To run: `python3 ./sort.py [input file] [child count]`

![Example3](Images/Example3.png "Shared Sort Example")

## 4. Daemon Sort

This program features a daemon, and a hybrid master slave process to sort text files on a shared folder.

To run: `python3 ./daemon.py` on two computers on the same network, sharing the same folder.

And: `python3 ./hybrid.py m 2` to run a (m)aster process with two slaves.

![Example4](Images/Example4.png "Daemon Sort Example")

## 5. Device Network

This program features routers that create devices, that create routing tables to each other.

To run: `python3 ./router.py 10 50 0,100,0,100`

Where the options are `[device count] [device strength] [startx],[maxx],[starty],[maxy]`.

![Example5](Images/Example5.png "Device Network Example")

## License

https://creativecommons.org/licenses/by/4.0/