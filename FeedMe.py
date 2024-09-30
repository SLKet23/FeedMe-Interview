import threading
import time
import queue
import os
import keyboard 

order_id = 1
order_queue = queue.PriorityQueue()
completed_orders = []
bots = []
lock = threading.Lock()
bot_statuses = []
command_running = True  # Flag to check if the main loop is running

# Order class
class Order:
    def __init__(self, priority, order_type, order_id):
        self.priority = priority
        self.order_type = order_type
        self.order_id = order_id

    def __lt__(self, other):
        return self.priority < other.priority


# Bot worker function
def bot_worker(bot_id, stop_event):
    while not stop_event.is_set():  # Keep running until the stop event is set
        try:
            with lock:
                bot_statuses[bot_id - 1] = f"Bot {bot_id}: Idle"  # Set bot status to Idle initially

            priority, current_order = order_queue.get(timeout=5)  # Get an order from the queue or timeout
            if stop_event.is_set():  # Stop the bot if requested
                order_queue.put((priority, current_order))  # Put the order back in the queue if stopping
                break

            # Update the bots list to reflect the current order being processed
            with lock:
                bots[bot_id - 1] = (bots[bot_id - 1][0], stop_event, current_order)  # Store current order

            # Processing countdown
            countdown_time = 10  # Set the countdown time
            with lock:
                bot_statuses[bot_id - 1] = f"Bot {bot_id}: Processing Order {current_order.order_id} ({current_order.order_type}) - Time left: {countdown_time} seconds"

            # Countdown loop
            while countdown_time > 0 and not stop_event.is_set():
                time.sleep(1)  # Sleep for 1 second
                countdown_time -= 1  # Decrease countdown time
                with lock:
                    bot_statuses[bot_id - 1] = f"Bot {bot_id}: Processing Order {current_order.order_id} ({current_order.order_type}) - Time left: {countdown_time} seconds"
                clear_screen()
                display_orders()  # Display the current orders and bot statuses

            if countdown_time == 0:
                with lock:
                    completed_orders.append(current_order)  # Add the completed order
                    bot_statuses[bot_id - 1] = f"Bot {bot_id}: Idle"
                    # Reset current order in the bots list
                    bots[bot_id - 1] = (bots[bot_id - 1][0], stop_event, None)  # Reset current order
                    clear_screen()
                    display_orders()  # Update display after finishing an order

            order_queue.task_done()  # Mark task as done
            
            # Check if there are no more orders to process
            if order_queue.empty():
                with lock:
                    bot_statuses[bot_id - 1] = f"Bot {bot_id}: Idle"  # Set to idle if no orders are left

        except queue.Empty:
            time.sleep(1)  # Wait for a while before checking again


# Add new order
def add_order(order_type):
    global order_id
    with lock:
        priority = 1 if order_type == "VIP" else 2
        order = Order(priority, order_type, order_id)
        order_queue.put((priority, order))
        print(f"Order {order_id} ({order_type}) added to queue")
        order_id += 1


# Manage bots
def add_bot():
    bot_id = len(bots) + 1
    stop_event = threading.Event()
    bot = threading.Thread(target=bot_worker, args=(bot_id, stop_event))
    bots.append((bot, stop_event, None))  # Store None as a placeholder for current order
    bot_statuses.append(f"Bot {bot_id}: Idle")
    bot.start()


def remove_bot():
    if bots:
        bot, stop_event, current_order = bots.pop()
        stop_event.set()  # Signal the bot to stop
        bot.join()  # Wait for the bot to stop
        bot_statuses.pop()

        # Check if the bot was processing an order
        if current_order is not None:
            # Re-add the order back to the queue
            with lock:
                order_queue.put((current_order.priority, current_order))  # Put back the order into the queue
                print(f"Order {current_order.order_id} ({current_order.order_type}) returned to queue")
        
        print(f"Bot {len(bots) + 1} removed")


# Clear screen
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


# Display orders and bots statuses
def display_orders():
    with order_queue.mutex:
        print("Welcome to McDonald's! Press the keys for actions: \n 1) New Normal \n 2) New VIP \n 3) New Bot \n 4) Remove Bot \n 5) Exit \n")
        print("\nPENDING Orders in Queue:\n===================")
        if order_queue.queue:
            for priority, order in sorted(order_queue.queue):
                print(f"- Order {order.order_id}: {order.order_type} (Priority: {priority})")
        else:
            print("No orders in queue.")

    print("\nCOMPLETED Orders:\n===================")
    if completed_orders:
        for order in completed_orders:
            print(f"- Order {order.order_id}: {order.order_type}")
    else:
        print("No completed orders.")

    print("\nBOT STATUSES:\n===================")
    if bot_statuses:
        for status in bot_statuses:
            print(status)
    else:
        print("No bots are running.")


# Handle key presses
def handle_key_presses():
    global command_running

    # Define key handlers
    keyboard.add_hotkey('1', lambda: add_order("Normal"))
    keyboard.add_hotkey('2', lambda: add_order("VIP"))
    keyboard.add_hotkey('3', add_bot)
    keyboard.add_hotkey('4', remove_bot)
    keyboard.add_hotkey('5', stop_program)

    # Keep listening for key presses
    while command_running:
        time.sleep(0.1) 

# Stop the program
def stop_program():
    global command_running
    command_running = False
    print("Thank you for using McDonald's!")


# Main loop
def main_loop():
    keyboard_thread = threading.Thread(target=handle_key_presses)
    keyboard_thread.start()  

    while command_running: 
        clear_screen() 
        display_orders()  
        time.sleep(1) 

    keyboard_thread.join()  


# Start the main loop and the bot system
if __name__ == "__main__":
    main_loop()  # Start the main loop


#pip install keyboard
