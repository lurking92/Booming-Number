import socket
import threading
import time
import random

HOST = '127.0.0.1'
PORT1 = 1234
PORT2 = 1235

# set up ip and port
BROADCAST_IP = '255.255.255.255'
BROADCAST_PORT1 = 4567
BROADCAST_PORT2 = 4568

# set up UDP connected
sock_broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# create the lock of threading
lock = threading.Lock()
condition = threading.Condition(lock)
game_over_event = threading.Event()

# counting the player online
current_player = 1

def introduce():
    while not game_over_event.is_set():
        str1 = "輸入數字1開始遊戲༼ つ◕◕ ༽つ\n數字範圍1-1000"
        sock_broadcast.sendto(str1.encode(), (BROADCAST_IP, BROADCAST_PORT1))
        sock_broadcast.sendto(str1.encode(), (BROADCAST_IP, BROADCAST_PORT2))
        print(f"Server broadcast: {str1}")
        time.sleep(3)  # broadcasting the rules every 3 sec.

# deal with the client guess online
def handle_client(conn, addr, id):
    global current_player
    try:
        while not game_over_event.is_set():
            with condition:
                while current_player != id and not game_over_event.is_set():
                    condition.wait()
                
                if game_over_event.is_set():
                    break

                conn.send(f"現在是你的回合，請輸入你的猜測: ".encode())

            data = conn.recv(1024)
            if not data:
                break

            with condition:
                if current_player == id:
                    game(conn, data.decode())
                    current_player = 2 if current_player == 1 else 1
                    condition.notify_all()
                else:
                    conn.send("還沒換你猜！".encode())

            print(f"[{id}]recv: {data.decode()}")
    
    finally:
        with lock:
            conn.send("遊戲已結束，感謝參與！".encode())  # finished the game and send the end message to each player
            conn.close()
            print(f"[{id}]Connection[address:{addr}] closed.", "(Current Client:0)\n")

# game rules
def game(conn, data):
    global ans, beg, en
    if data.isdigit():
        guess = int(data)
    else:
        msg = "請輸入數字(整數)"
        conn.send(msg.encode())
        return
    
    if guess == ans:
        msg = "(｡◕∀◕｡)恭喜答對了~(灬ºωº灬)"
        conn.send(msg.encode())
        game_over_event.set()
        broadcast_end()
    elif guess > ans and guess <= en:
        en = guess
        msg = f"猜的數字太大了，範圍是 {beg} 到 {en}"
        conn.send(msg.encode())
        broadcast_range(beg, en)
    elif guess < ans and guess >= beg:
        beg = guess
        msg = f"猜的數字太小了，範圍是 {beg} 到 {en}"
        conn.send(msg.encode())
        broadcast_range(beg, en)
    else:
        msg = "猜的數字超出範圍"
        conn.send(msg.encode())

def broadcast_range(beg, en):
    msg = f"當前有效數字範圍是 {beg} 到 {en}"
    sock_broadcast.sendto(msg.encode(), (BROADCAST_IP, BROADCAST_PORT1))
    sock_broadcast.sendto(msg.encode(), (BROADCAST_IP, BROADCAST_PORT2))
    print(f"Server broadcast: {msg}")

def broadcast_end():
    msg = "遊戲已結束，感謝參與！"
    sock_broadcast.sendto(msg.encode(), (BROADCAST_IP, BROADCAST_PORT1))
    sock_broadcast.sendto(msg.encode(), (BROADCAST_IP, BROADCAST_PORT2))
    print(f"Server broadcast: {msg}")

def reset_game():
    global ans, beg, en
    ans = random.randrange(1, 1000)
    print(ans)
    beg = 1
    en = 1000

# reset
reset_game()

# set up and binding 2 TCP connecting
sockets = []
for port in (PORT1, PORT2):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, port))
    s.listen(5)
    sockets.append(s)
    print(f'Server start at: {HOST}:{port}')

print('Server waits.')

# recieved the connecting from two clients
conn1, addr1 = sockets[0].accept()
conn2, addr2 = sockets[1].accept()

# creating the threads and handle with each client
thread1 = threading.Thread(target=introduce)    # broadcast the rules
thread2 = threading.Thread(target=handle_client, args=(conn1, addr1, 1))
thread3 = threading.Thread(target=handle_client, args=(conn2, addr2, 2))

# run the threads
thread1.start()
thread2.start()
thread3.start()

print(f"New client with address:{addr1}", f"(Current Client:1)")
print(f"New client with address:{addr2}", f"(Current Client:2)")

# wait for the game over
game_over_event.wait()

# finished the threads
thread1.join()
thread2.join()
thread3.join()
print("遊戲結束")

# prompt player to leave
input("Press any key to exit...")