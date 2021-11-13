from threading import Thread
import time

thread_running = True


def my_forever_while():
    global thread_running

    start_time = time.time()

    # run this while there is no input
    while thread_running:
        time.sleep(0.1)

        if time.time() - start_time >= 5:
            start_time = time.time()
            print('Another 5 seconds has passed')


def take_input():
    user_input = input('Type user input: ')
    # doing something with the input
    print('The user input is: ', user_input)


if __name__ == '__main__':
    t1 = Thread(target=my_forever_while)
    t2 = Thread(target=take_input)

    t1.start()
    t2.start()

    t2.join()  # interpreter will wait until your process get completed or terminated
    thread_running = False
    print('The end')
