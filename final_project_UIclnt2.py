import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
from PIL import Image, ImageTk, ImageSequence

# Configure broadcast address and port
BROADCAST_IP = '255.255.255.255'
BROADCAST_PORT = 4568  # Change to 4568 for the second client
SERVER_PORT = 1235     # Change to 1235 for the second client
MAXLINE = 1024

# Initialize UDP socket for receiving broadcast
broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
broadcast_sock.bind(('', BROADCAST_PORT))  # Bind broadcast socket to broadcast port

# Initialize TCP socket for server communication
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Variables to store event control
game_over_event = threading.Event()
your_turn_event = threading.Event()

received_messages = set()

def receive_broadcast():
    while not game_over_event.is_set():
        data, addr = broadcast_sock.recvfrom(MAXLINE)
        message = data.decode()
        if message not in received_messages:
            received_messages.add(message)
            update_chat_log(f"Received game rule: {message}")
        if message == "遊戲已結束，感謝參與！":
            game_over_event.set()
            break

def communicate_with_server():
    global game_over_event, your_turn_event
    server_host = '127.0.0.1'  # Change to your server IP address
    server_addr = (server_host, SERVER_PORT)

    try:
        server_sock.connect(server_addr)
        update_chat_log("client2 connected to server.")
        
        # Receive messages from the server
        while not game_over_event.is_set():
            data = server_sock.recv(MAXLINE)
            if not data:
                break
            message = data.decode()
            update_chat_log(message)
            if "現在是你的回合" in message:
                your_turn_event.set()
            elif "遊戲已結束，感謝參與！" in message:
                game_over_event.set()
                break
            elif "恭喜答對了" in message:
                show_explosion_gif()
    except Exception as e:
        update_chat_log(f"Error communicating with server: {e}")

def send_guesses_to_server():
    while not game_over_event.is_set():
        your_turn_event.wait()
        guess = guess_entry.get()
        if guess.isdigit():
            server_sock.send(guess.encode())
            guess_entry.delete(0, tk.END)
        else:
            update_chat_log("請輸入有效的數字。")
        your_turn_event.clear()

def update_chat_log(message):
    chat_log.config(state=tk.NORMAL)
    chat_log.insert(tk.END, message + '\n', ('blue_text',))
    chat_log.config(state=tk.DISABLED)
    chat_log.yview(tk.END)

def on_send_click():
    guess = guess_entry.get()
    if guess.isdigit():
        server_sock.send(guess.encode())
        guess_entry.delete(0, tk.END)
    else:
        update_chat_log("請輸入有效的數字。")

def show_explosion_gif():
    explosion_window = tk.Toplevel(root)
    explosion_window.title("Explosion")
    
    gif_label = tk.Label(explosion_window)
    gif_label.pack()

    gif = Image.open("explosion.gif")
    frames = [ImageTk.PhotoImage(frame) for frame in ImageSequence.Iterator(gif)]

    def animate(idx=0):
        gif_label.config(image=frames[idx])
        idx = (idx + 1) % len(frames)
        explosion_window.after(180, animate, idx)  # Adjust delay as needed

    animate()
    explosion_window.after(4500, explosion_window.destroy)  # Close after 2 seconds

# Create the main window
root = tk.Tk()
root.title("猜數字遊戲")

# Set the window size
root.geometry('500x400')

# Load the background image
bg_image = Image.open("background.jpg")  
bg_image = bg_image.resize((500, 400), Image.Resampling.LANCZOS)
bg_photo = ImageTk.PhotoImage(bg_image)

# Create a canvas to hold the background image
canvas = tk.Canvas(root, width=500, height=400)
canvas.pack(fill="both", expand=True)
canvas.create_image(0, 0, image=bg_photo, anchor="nw")

# Create a chat log to display messages
chat_log = scrolledtext.ScrolledText(root, state=tk.DISABLED, width=50, height=15, bg='#ADD8E6', fg='#000', font=('Arial', 12))
chat_log.tag_config('blue_text', background='#ADD8E6')
chat_log_window = canvas.create_window(20, 20, anchor="nw", window=chat_log)

# Create an entry box for user to input guesses
guess_entry = tk.Entry(root, width=40, bg='#fff', fg='#000', font=('Arial', 12))
guess_entry_window = canvas.create_window(20, 320, anchor="nw", window=guess_entry)

# Create a send button
send_button = tk.Button(root, text="Send", command=on_send_click, bg='#4CAF50', fg='#fff', font=('Arial', 12))
send_button_window = canvas.create_window(380, 320, anchor="nw", window=send_button)

# Start thread to receive broadcasts
receive_thread = threading.Thread(target=receive_broadcast)
receive_thread.daemon = True
receive_thread.start()

# Start thread to communicate with the server
communication_thread = threading.Thread(target=communicate_with_server)
communication_thread.start()

# Start thread to send guesses to the server
guess_thread = threading.Thread(target=send_guesses_to_server)
guess_thread.start()

# Start the Tkinter main loop
root.mainloop()

# Wait for the game to end
communication_thread.join()
guess_thread.join()

# Close sockets
broadcast_sock.close()
server_sock.close()