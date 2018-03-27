import sys
import threading
import time
import queue

def add_input(input_queue):
    while True:
        input_queue.put(sys.stdin.read(1))

def foobar():
    input_queue = queue.Queue()

    input_thread = threading.Thread(target=add_input, args=(input_queue,))
    input_thread.daemon = True
    input_thread.start()

    last_update = time.time()
    while True:
	
        for i in range(3):
            print("hey man")
            time.sleep(1)

        if time.time()-last_update>0.5:
            sys.stdout.write(".")
            last_update = time.time()

        if not input_queue.empty():
            print("\ninput:", input_queue.get())

foobar()
