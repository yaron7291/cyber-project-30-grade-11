__author__ = 'yaron'

from operator import truediv
import sys
from tcp_by_size import send_with_size, recv_by_size
import threading, socket, pygame
sockudp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address_tcp = ('127.0.0.1', 1233)
server_address_udp = ('127.0.0.1', 1234)
sock.connect(server_address_tcp)

client_id = None
enemy_id = None
room_id = None
player = None
enemy = None
turret = None
enemy_turret = None

pygame.init()
screen_width = 1400
screen_height = 800
screen = pygame.display.set_mode((screen_width, screen_height))
clock = pygame.time.Clock()
fps = 60
tanksize = 50


def draw_button(screen, text, x, y, w, h, color, hover_color):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()

    # בדיקה אם העכבר על הכפתור
    rect = pygame.Rect(x, y, w, h)
    if rect.collidepoint(mouse):
        pygame.draw.rect(screen, hover_color, rect)
        if click[0] == 1:  # לחיצה שמאלית
            return True
    else:
        pygame.draw.rect(screen, color, rect)

    # ציור הטקסט במרכז הכפתור
    font = pygame.font.SysFont("Arial", 30)
    text_surf = font.render(text, True, "white")
    screen.blit(text_surf, (x + (w / 2 - text_surf.get_width() / 2), y + (h / 2 - text_surf.get_height() / 2)))
    return False

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
        self.width = 80
        self.height = 10
        self.original_image = pygame.Surface((self.width * 2, self.width * 2), pygame.SRCALPHA)
        if self.client_id == 1:
            color = "red"
        else:
            color = "black"
        if self.client_id == 1:
            pygame.draw.rect(self.original_image, color,(self.width, self.width - self.height // 2, self.width, self.height))
        else:
            pygame.draw.rect(self.original_image, color, (0, self.width - self.height // 2, self.width, self.height))

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
                if self.angle < -90:
                    self.angle = -90
                if self.angle > 0:
                    self.angle = 0
            else:
                if keys[pygame.K_UP]:
                    self.angle += 1
                if keys[pygame.K_DOWN]:
                    self.angle -= 1
                self.angle = max(0, min(90, self.angle))

            if old_angle != self.angle:
                self.angle_changed = True

        self.image = pygame.transform.rotate(self.original_image, self.angle)
        if self.client_id == 1:
            pivot_x = self.parent.rect.right -22
        else:
            pivot_x = self.parent.rect.x + 20
        pivot_y = self.parent.rect.y + 15
        self.rect = self.image.get_rect(center=(pivot_x, pivot_y))


class Tank(pygame.sprite.Sprite):
    def __init__(self, client_id):
        super().__init__()
        original_img = pygame.image.load("images/tank.png").convert_alpha()
        self.base_image = pygame.transform.scale(original_img, (100, 37))
        self.client_id = client_id
        if self.client_id == 1:
            self.image = pygame.transform.flip(self.base_image, True, False)
        else:
            self.image = self.base_image

        self.rect = self.image.get_rect()
        if self.client_id == 1:
            self.rect.right = 0
        else:
            self.rect.right = screen_width
        self.rect.bottom = screen_height - 20
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
        distance_from_border = 50
        bar_precent = int(precent * bar_width)
        if self.client_id == 1:
            bar_x = distance_from_border
        else:
            bar_x = screen_width - bar_width - distance_from_border
        bar_y = 40
        pygame.draw.rect(surface, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        color = (0, 255, 0) if self.hp > 30 else (255, 165, 0)  # משנה צבע בחיים נמוכים
        pygame.draw.rect(surface, color, (bar_x, bar_y, bar_precent, bar_height))



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
            if enemy_id == 1:
                pivot_x = enemy.rect.right - 22
            else:
                pivot_x = enemy.rect.x + 22
            pivot_y = enemy.rect.y + 15
            enemy_turret.rect = enemy_turret.image.get_rect(center=(pivot_x, pivot_y))
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


def show_game_over(screen, result_text, color):
    font_big = pygame.font.SysFont("Arial", 100, bold=True)
    font_small = pygame.font.SysFont("Arial", 50)

    for i in range(5, 0, -1):
        screen.fill("black")
        text_surf = font_big.render(result_text, True, color)
        screen.blit(text_surf, (screen_width // 2 - text_surf.get_width() // 2, screen_height // 3))
        countdown_text = f"Returning to menu in {i}..."
        count_surf = font_small.render(countdown_text, True, "white")
        screen.blit(count_surf, (screen_width // 2 - count_surf.get_width() // 2, screen_height // 2))

        pygame.display.flip()
        pygame.time.delay(1000)
def listen_to_server():
    global running, room_id, client_id, player, turret, enemy, enemy_id, enemy_turret, all_sprites, current_state ,player_shots, enemy_shots, bullets, bullet_temp
    while running:
        try:
            tcpdata = recv_by_size(sock)
            if tcpdata:
                msg = tcpdata.decode("utf-8")
                tcparts = msg.split("|")
                print("tcp revc",msg)
                if msg == "EXIT":
                    current_state = STATE_MENU
                if tcparts[0] == "LOSE":
                    loseid = int(tcparts[1])
                    if loseid == client_id:
                        show_game_over(screen, "YOU LOST!", (255, 0, 0))  # אדום
                    if loseid == enemy_id:
                        show_game_over(screen, "YOU WIN!", (0, 255, 0))  # ירוק
                    current_state = STATE_MENU
                    room_id = None

                if tcparts[0] == "JOIN_SUCCESS":

                    room_id = tcparts[1]
                    id_data= recv_by_size(sock)
                    if id_data:
                        client_id = int(id_data.decode())
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
                        enemy_turret = Turret(enemy, enemy_id)
                        enemy_turret.turret_color = "black"

                        all_sprites.add(enemy)
                        all_sprites.add(bullet_temp)
                        all_sprites.add(enemy_turret)
                        player_shots = 0
                        enemy_shots = 0
                        print(f"room update to : {room_id} client id to :{client_id}")
                        msg_udp = f"hello|{client_id}|{room_id}"
                        sockudp.sendto(msg_udp.encode(), server_address_udp)

                if msg == "START":
                    current_state = STATE_GAME
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
all_sprites = pygame.sprite.Group()
player_shots = 0
enemy_shots = 0
running = True
threading.Thread(target=listen_to_server, daemon=True).start()
STATE_MENU = "MENU"
STATE_LOBBY = "LOBBY"
STATE_GAME = "GAME"
current_state = STATE_MENU
room_code_input = ""
typing_mode = False
while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if room_id is not None:
                msg_Exit = f"EXIT|{client_id}|{room_id}"
                send_with_size(sock, msg_Exit.encode())
            running = False
        if typing_mode and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                send_with_size(sock, f"JOIN_PRIVATE|{room_code_input}")
                typing_mode = False
                current_state = STATE_LOBBY
            elif event.key == pygame.K_BACKSPACE:
                room_code_input = room_code_input[:-1]
            else:
                if len(room_code_input) < 4:
                    room_code_input += event.unicode

    if current_state == STATE_MENU:
        screen.fill("black")
        if draw_button(screen, "Random Match", 550, 200, 300, 50, "blue", "cyan"):
            send_with_size(sock, "MATCHMAKE")
            current_state = STATE_LOBBY

        if draw_button(screen, "Create Private Lobby", 550, 300, 300, 50, "green", "lime"):
            send_with_size(sock, "CREATE_PRIVATE")
            current_state = STATE_LOBBY

        if draw_button(screen, "Join Private", 550, 400, 300, 50, "red", "orange"):
            typing_mode = True
            pass

        if typing_mode:
            font = pygame.font.SysFont("monospace", 20)
            img = font.render(f"Enter code: {room_code_input}", True, (255, 255, 255))
            screen.blit(img, (550, 470))


    elif current_state == STATE_LOBBY:
            screen.fill("black")
            font = pygame.font.SysFont("Arial", 50)
            text = font.render("Waiting for second player...", True, "white")
            screen.blit(text, (screen_width // 2 - 250, screen_height // 2))
            if room_id:
                font_small = pygame.font.SysFont("Arial", 40)
                code_text = font_small.render(f"Enter code: {room_id}", True, (255, 255, 255))
                screen.blit(code_text, (screen_width // 2 - code_text.get_width()// 2, screen_height // 2+ 150))


    elif current_state == STATE_GAME:
        if player is None or turret is None:
            continue
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
        sockudp.setblocking(False)
        try:
            while True:
                data, addr = sockudp.recvfrom(1024)
                if data:
                    data_str = data.decode("utf-8")
                    update_data(data_str)
                    print("udpp" + data_str)
        except (BlockingIOError, socket.error):
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
