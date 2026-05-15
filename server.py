__author__ = 'yaron'

from contextlib import nullcontext
from math import expm1
from traceback import format_exc

from tcp_by_size import send_with_size, recv_by_size
import socket, threading ,time , math
rooms_lock = threading.Lock()
all_to_die = False
fps = 60
client_shot = 1

all_clients = []
class GameRoom:
    def __init__(self, roomd_id):
        self.roomd_id = roomd_id
        self.players = []
        self.udp_players = {}
        self.clients_info = {}
        self.game_started = False
        self.bullet_countre = 0

    def add_player(self, player):
        if len(self.players) < 2:
            self.players.append(player)
            return True
        return False

class PlayerData:
    def __init__(self, color, x, y):
        self.x = x
        self.y = y
        self.angle = 0
        self.hp = 100
        self.is_turn = False
        self.color = color
        self.hp = 100


def shot(client_id, room_id):
    global client_shot
    client_shot += 1
    t = threading.Thread(target=shot_logic, args=(client_id, client_shot, room_id))
    t.daemon = True
    t.start()
    print(f"{client_shot} new shot1")


def shot_logic(client_id, client_shot, room_id):
    if room_id not in all_rooms:
        print(f"Error: Room {room_id} not found!")
        return

    room = all_rooms[room_id]
    client_id_str = str(client_id)
    if client_id_str not in room.clients_info:
        print(f"Error: Client {client_id_str} not found!")
        return
    playerdata = room.clients_info[client_id_str]
    other_id = "2" if client_id_str == "1" else "1"
    if other_id not in room.clients_info:
        print(f"Error: Client id {client_id_str} not found!")
        return
    xi = float(playerdata['x'])
    yi = float(playerdata['y'])
    angle = abs(float(playerdata['angle']))
    rad_angle = math.radians(angle)
    g = 4
    clock = float(1/60)
    force = 80
    t_temp = 0
    t_total = abs((-2 * force * math.sin(rad_angle) ) / g)
    y_temp = -100
    x_temp = -100
    if client_id_str == "1":
        direction = -1
    else: direction = 1
    while t_temp <= t_total:
        ## physics with udi the best teacher
        x_temp = xi - force * math.cos(rad_angle) * t_temp * direction
        y_temp = yi - force * abs(math.sin(rad_angle)) * t_temp + g * math.pow(t_temp, 2) / 2
        to_send = f"shoted|{x_temp}|{y_temp}|{client_id}|{client_shot}|1"
        playerdataother = room.clients_info[other_id]
        otherx = float(playerdataother['x'])
        othery = float(playerdataother['y'])
        for target_id, target_addr in room.udp_players.items():
            udp_sock.sendto(to_send.encode(), target_addr)
        t_temp = t_temp + clock
        time.sleep(clock)
        ## בדיקה אם הכדור בתוך הטווח שבו הטנק של היריב
        if otherx - 50 < x_temp < otherx + 50 and othery - 15< y_temp < othery + 15:
            print("Hited")
            print(f"before hp : {float(room.clients_info[other_id]['hp'])}")
            room.clients_info[other_id]['hp'] -= 10
            gotshotmsg = f"hit|{other_id}|{float(room.clients_info[other_id]['hp'])}"
            for Player_tcp_socket in room.players:
                try:
                    send_with_size(Player_tcp_socket, gotshotmsg.encode())
                except:
                    pass

            print(f"after hit msg: {gotshotmsg}")
            t_temp = t_total + 1
            if room.clients_info[other_id]['hp'] <= 0:
                msglose = f"LOSE|{other_id}"
                for Player_tcp_socket in room.players:
                    try:
                        send_with_size(Player_tcp_socket, msglose.encode())
                    except:
                        pass
                time.sleep(1)
                if room_id in all_rooms:
                    del all_rooms[room_id]
                    print(f"rome {room_id} closed and deleted!")

        for target_id, target_addr in room.udp_players.items():
            udp_sock.sendto(to_send.encode(), target_addr)
        t_temp = t_temp + clock * 10
        time.sleep(clock)
    stopmsg = f"shoted|{x_temp}|{y_temp}|{client_id}|{client_shot}|0"
    for target_id, target_addr in room.udp_players.items():
        udp_sock.sendto(stopmsg.encode(), target_addr)
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.bind(('0.0.0.0', 1234))
all_rooms = {}


def handle_udp_communication():
    print("UDP listener started on port 1234")

    while True:
        try:
            data, addr = udp_sock.recvfrom(1024)
            msg = data.decode()
            parts = msg.split("|")
            print("udpp" + msg)

            if parts[0] == "hello":
                c_id = parts[1]
                room_id = parts[2]
                if room_id in all_rooms:
                    all_rooms[room_id].udp_players[c_id] = addr
                    print(f"Player {c_id} registered UDP in room {room_id}")

            elif parts[0] == "move":
                client_id = parts[1]
                room_id = parts[2]
                if room_id in all_rooms:
                    room = all_rooms[room_id]
                    if client_id in room.clients_info:

                        x = parts[3]
                        y = parts[4]
                        angle = parts[5]
                        room.clients_info[client_id]['x'] = x
                        room.clients_info[client_id]['y'] = y
                        room.clients_info[client_id]['angle'] = angle
                        print(f"Update: Player {client_id} is at ({x}, {y}) angle {angle} id {client_id}")
                        to_send = f"moved|{x}|{y}|{angle}|{client_id}"
                        for target_id, target_addr in room.udp_players.items():
                            if str(client_id) != target_id:
                                udp_sock.sendto(to_send.encode(), target_addr)

        except ConnectionResetError:
            continue
        except Exception as e:
            print(f"UDP Error: {e}")
            continue

import random
import string

def generate_room_id():
    return ''.join(random.choices(string.digits, k=4))


def handle_client(sock, tid, addr):
    room_id = None
    while room_id is None:
        try:
            data = recv_by_size(sock)
            msg = data.decode()
            parts = msg.split("|")

            target_room_obj = None

            if parts[0] == "CREATE_PRIVATE":
                new_id = generate_room_id()
                all_rooms[new_id] = GameRoom(new_id)
                target_room_obj = all_rooms[new_id]
                print(f"Created private room: {new_id}")

            elif parts[0] == "MATCHMAKE":
                with rooms_lock:
                    to_delete = [rid for rid, r in list(all_rooms.items()) if len(r.players) == 0]
                    for rid in to_delete:
                        del all_rooms[rid]
                    found = False
                    target_room_obj = None
                    for r_id, r_obj in all_rooms.items():
                        if len(r_obj.players) == 1:
                            target_room_obj = r_obj
                            found = True
                            print(f"joined existing room: {r_id}")
                            break

                    if not found:
                        new_id = generate_room_id()
                        all_rooms[new_id] = GameRoom(new_id)
                        target_room_obj = all_rooms[new_id]
                if target_room_obj:
                    if target_room_obj.add_player(sock):
                        room_id = target_room_obj.roomd_id

                        send_with_size(sock, f"JOIN_SUCCESS|{room_id}".encode())

                        current_room = all_rooms[room_id]
                        my_id_in_room = str(len(current_room.players))
                        current_room.clients_info[my_id_in_room] = {'x': 0, 'y': 0, 'angle': 0, 'hp': 100.0}

                        send_with_size(sock, my_id_in_room.encode())

                        if len(current_room.players) == 2:
                            for s in current_room.players:
                                send_with_size(s, "START".encode())
                    else:
                        send_with_size(sock, "ERROR|Room full".encode())

            elif parts[0] == "JOIN_PRIVATE":
                code = parts[1]
                if code in all_rooms:
                    target_room_obj = all_rooms[code]
                else:
                    send_with_size(sock, "ERROR|Room not found".encode())
                    continue



        except Exception as e:
            print(f"Error in menu phase: {e}")
            break
    global all_to_die
    finish = False
    print(f'New Client number {tid} from {addr}')


    while not finish:
        if all_to_die:
            break
        try:
            byte_data = recv_by_size(sock)
            if byte_data == b'':
                break
            request_str = byte_data.decode("utf8")
            parts = request_str.split("|")
            request_code = parts[0]
            print(request_code)
            if request_code == 'EXIT':
                exitmsg = f"EXIT"
                room_id_str= parts[2]
                if room_id_str and room_id_str in all_rooms:
                    room = all_rooms[room_id_str]
                    for sockt in list(room.players):
                        try:
                            send_with_size(sockt, exitmsg.encode())
                            print(exitmsg)
                        except Exception as e:
                            print(e)
                    del all_rooms[room_id_str]
                    print(f"rome {room_id_str} closed and deleted!")
                room_id = None
                break

            if request_code == 'shot':
                client_id = parts[1]
                print("shot get")
                room_id = parts[2]
                shot(client_id ,room_id)
            if finish:
                time.sleep(0.5)
                break
        except socket.error as err:
            break
    sock.close()

def main():
    global all_to_die
    srv_sock = socket.socket()
    srv_sock.bind(('0.0.0.0', 1233))
    srv_sock.listen(2)
    srv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    i = 1
    udp_tread = threading.Thread(target=handle_udp_communication)
    udp_tread.deamon = True
    udp_tread.start()
    while True:
        cli_sock, addr = srv_sock.accept()
        all_clients.append(cli_sock)
        t = threading.Thread(target=handle_client, args=(cli_sock, str(i), addr))
        t.start()



        i += 1
if __name__ == '__main__':
    main()