__author__ = 'yaron'

from operator import truediv
import sys
from tcp_by_size import send_with_size, recv_by_size
import threading, socket, pygame
room_id = "67"
sockudp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address_tcp = ('127.0.0.1', 1233)
server_address_udp = ('127.0.0.1', 1234)
sock.connect(server_address_tcp)
try:
    msg_join = f"JOIN|{room_id}"
    send_with_size(sock, msg_join)
    join_response = recv_by_size(sock).decode()
    print("join response", join_response)
    data = recv_by_size(sock)
    client_id = int(data.decode())
    print("Client ID:", client_id)
    sock.setblocking(False)
    print("Connected to server!")
    msg = f"hello|{client_id}|{room_id}"
    sockudp.sendto(msg.encode(), server_address_udp)
    print("UDP Send message:", msg)
    sockudp.setblocking(False)
except:
    print("Connection failed")
    sys.exit()

game_started = False
pygame.init()
screen_width = 1400
screen_height = 800
screen = pygame.display.set_mode((screen_width, screen_height))
clock = pygame.time.Clock()
fps = 60
tanksize = 50


class Bullet(pygame.sprite.Sprite):
    def __init__(self, bullet_id):
        global client_id
        super().__init__()
        self.client_id = bullet_id
        self.radius = tanksize / 2
        self.width = int(tanksize / 4)
        self.height = int(tanksize * 1.5)
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        if self.client_id == client_id:
            color = "red"
        else:
            color = "black"
        pygame.draw.circle(self.image, color, (self.radius, self.radius), self.radius)
        self.rect = self.image.get_rect()
        self.rect.center = (-100, -100)

    def update(self):
        pass


class Turret(pygame.sprite.Sprite):
    def __init__(self, parent_tank, client_id):
        super().__init__()
        self.client_id = client_id
        self.parent = parent_tank
        self.width = int(tanksize / 4)
        self.height = int(tanksize * 1.5)
        self.original_image = pygame.Surface((self.width, self.height * 2), pygame.SRCALPHA)
        if self.client_id == 1:
            color = "red"
        else:
            color = "black"
        pygame.draw.rect(self.original_image, color, (0, 0, self.width, self.height))
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.angle = 0
        self.angle_changed = False

    def update(self):
        if self.client_id == client_id:
            keys = pygame.key.get_pressed()
            old_angle = self.angle
            if self.client_id == 2:
                if keys[pygame.K_UP]:
                    self.angle -= 1
                if keys[pygame.K_DOWN]:
                    self.angle += 1
                if self.angle < 0:
                    self.angle = 0
                if self.angle > 90:
                    self.angle = 90
            else:
                if keys[pygame.K_UP]:
                    self.angle += 1
                if keys[pygame.K_DOWN]:
                    self.angle -= 1
                if self.angle > 0:
                    self.angle = 0
                if self.angle < -90:
                    self.angle = -90
            if old_angle != self.angle:
                self.angle_changed = True  # --- מעדכנים שצריך לשלוח לשרת ---
            self.image = pygame.transform.rotate(self.original_image, self.angle)
            self.rect = self.image.get_rect(center=self.parent.rect.center)
        else: pass

class Tank(pygame.sprite.Sprite):
    def __init__(self, client_id):
        super().__init__()
        self.client_id = client_id
        self.tank_color = "green"
        self.image = pygame.Surface((tanksize, tanksize), pygame.SRCALPHA)
        self.draw_tank()
        self.rect = self.image.get_rect()
        if self.client_id == 1:
            self.rect.right = 0
        else:
            self.rect.right = screen_width
        self.rect.centery = screen_height - tanksize + 10
        self.speed = 2
        self.moved = False
        self.shots = 0
        self.shoting = False
        self.shoting_avb = True
        self.hp = 100


    def draw_hprect(self, surface):
        hp = self.hp
        max_hp = 100.0
        precent = max(0, min(hp / max_hp, 1))
        bar_width = 200
        bar_height = 50
        bar_precent = int(precent * bar_width)
        if self.client_id == 1:
            bar_x = 0
        else:
            bar_x = screen_width - 220
        bar_y = 75
        pygame.draw.rect(surface, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        color = (0, 255, 0) if self.hp > 30 else (255, 165, 0)  # משנה צבע בחיים נמוכים
        pygame.draw.rect(surface, color, (bar_x, bar_y, bar_precent, bar_height))

    def draw_tank(self):
        self.image.fill((0, 0, 0, 0))
        pygame.draw.rect(self.image, self.tank_color, (0, 0, tanksize, tanksize))

    def update(self):
        if self.client_id == client_id:
            keys = pygame.key.get_pressed()
            old_x = self.rect.x
            if not keys[pygame.K_SPACE]:
                self.shoting = False
            if keys[pygame.K_SPACE]:
                if self.shoting_avb:
                    self.shoting = True
                    self.shots += 1
                    self.shoting_avb = False
            if keys[pygame.K_LEFT]:
                self.rect.x -= self.speed
            if keys[pygame.K_RIGHT]:
                self.rect.x += self.speed
            if self.client_id == 1:
                if self.rect.left < 0:
                    self.rect.left = 0
                if self.rect.right > int(screen_width // 4):
                    self.rect.right = int(screen_width // 4)
            else:
                if self.rect.right > screen_width:
                    self.rect.right = screen_width
                if self.rect.left < screen_width - int(screen_width // 4):
                    self.rect.left = screen_width - int(screen_width // 4)
            if old_x != self.rect.x:
                self.moved = True
        else: pass


def update_data(data):
    parts = data.split("|")
    print("update_data", data)
    if parts[0] == "moved":
        recv_id = int(parts[4])
        if recv_id == enemy_id:
            enemy.rect.x = int(parts[1])
            print("new x", parts[1])
            enemy.rect.y = int(parts[2])
            print("new y", parts[2])
            enemy_turret.angle = int(parts[3])
            temp_id = int(parts[4])
            enemy_turret.image = pygame.transform.rotate(enemy_turret.original_image, enemy_turret.angle)
            enemy_turret.rect = enemy_turret.image.get_rect(center=enemy.rect.center)
    if parts[0] == "shoted":

        client_shots = int(parts[4])
        clientid = int(float(parts[3]))
        x = int(float(parts[1]))
        y = int(float(parts[2]))
        client_shots = int(parts[4])
        if client_shots not in bullets:
            temp_bullet = Bullet(client_id)
            bullets[client_shots] = temp_bullet
            all_sprites.add(temp_bullet)
            print(f"{client_shots} new shot")
        bullets[client_shots].rect.x = x
        bullets[client_shots].rect.y = y
        bullets[client_shots].clientid = clientid
        print(f"y:{bullet_temp.rect.y}, x:{bullet_temp.rect.x}, id:{bullet_temp.client_id}")
        if parts[5] == "0":
            if clientid == client_id:
                player.shoting_avb = True
            bullets[client_shots].kill()
            del bullets[client_shots]


def listen_to_server():
    global running, game_started
    while running:
        try:
            tcpdata = recv_by_size(sock)
            if tcpdata:
                msg = tcpdata.decode("utf-8")
                tcparts = msg.split("|")
                print("tcp revc",msg)
                if msg == "EXIT":
                    game_started = False

                if msg == "START":
                    game_started = True
                    print("game started")
                    continue
                if tcparts[0] == "hit":
                    got_hit_id = tcparts[1]
                    newhp = tcparts[2]
                    if int(got_hit_id) == int(client_id):
                        player.hp = float(newhp)
                        print(f"client new hp: {player.hp}")
                    if int(got_hit_id) == int(enemy_id):
                        enemy.hp = float(newhp)
                        print(f"enemy new hp: {enemy.hp}")


        except BlockingIOError:

            pass
        except Exception as e:
            print(f"Error receiving: {e}")


player = Tank(client_id)
turret = Turret(player, client_id)
all_sprites = pygame.sprite.Group()
all_sprites.add(player)
all_sprites.add(turret)

if client_id == 1:
    enemy_id = 2
else:
    enemy_id = 1
bullet_temp = Bullet(client_id)
bullets = {}
enemy = Tank(enemy_id)
enemy.tank_color = "red"
enemy.draw_tank()

enemy_turret = Turret(enemy, enemy_id)
enemy_turret.turret_color = "black"
all_sprites.add(enemy_turret)
all_sprites.add(enemy)
all_sprites.add(bullet_temp)

player_shots = 0
enemy_shots = 0
running = True
threading.Thread(target=listen_to_server, daemon=True).start()

while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            msg_Exit = f"EXIT|{client_id}|{room_id}"
            send_with_size(sock, msg_Exit)
            running = False
    if not game_started:
        screen.fill("black")
        font = pygame.font.SysFont("Arial", 50)
        text = font.render("Waiting for second player...", True, "white")
        screen.blit(text, (screen_width // 2 - 250, screen_height // 2))
        pygame.display.flip()
        clock.tick(fps)
        continue  # מדלג על שאר הלולאה (תנועה, ירי וכו')
    all_sprites.update()
    if player.moved or turret.angle_changed:
        msg = f"move|{client_id}|{room_id}|{player.rect.x}|{player.rect.y}|{turret.angle}"
        sockudp.sendto(msg.encode(), server_address_udp)
        player.moved = False
        turret.angle_changed = False


    if player.shots > player_shots:
        msg_shot = f"shot|{client_id}|{room_id}|{player.shots}"
        send_with_size(sock, msg_shot)
        player_shots = player.shots
    player.moved = False
    turret.angle_changed = False
    try:
        while True:
            data, addr = sockudp.recvfrom(1024)
            if data:
                data_str = data.decode("utf-8")
                update_data(data_str)
                print("udpp" + data_str)
    except BlockingIOError:

        pass
    except Exception as e:
        print(f"Error receiving: {e}")
    screen.fill("blue")
    all_sprites.draw(screen)
    enemy.draw_hprect(screen)
    player.draw_hprect(screen)
    pygame.display.flip()
    clock.tick(fps)
pygame.quit()
