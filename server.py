import socket
import time
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker
import pygame

pygame.init()
WIDTH_ROOM, HEIGHT_ROOM = 4000, 4000
WIDTH_SERVER, HEIGHT_SERVER = 300, 300
screen = pygame.display.set_mode((WIDTH_SERVER, HEIGHT_SERVER))
FPS = 250

pygame.display.set_caption("Сервер")
clock = pygame.time.Clock()
main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
main_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
main_socket.bind(("26.98.85.90", 11000))
main_socket.setblocking(False)
main_socket.listen(5)
print("Сервер запущен")
engine = create_engine("postgresql+psycopg2://postgres:1234@localhost/bacteria")
Session = sessionmaker(bind=engine)
Base = declarative_base()
s = Session()
players = {}


def filter2(vector):
    first = None
    for num, sign in enumerate(vector):
        if sign == "<":
            first = num
        if sign == ">" and first is not None:
            second = num
            vector = vector[first + 1:second]  # расшифровка
            vector = vector.split(",")
            vector = list(map(float, vector))
            return vector
    return ""


def find_color(info: str):
    first = None
    for num, sign in enumerate(info):
        if sign == "<":
            first = num
        if sign == ">" and first is not None:
            second = num
            result = info[first + 1:second].split(",")
            return result
    return ""


class Player(Base):
    __tablename__ = "gamers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(250))
    address = Column(String)
    x = Column(Integer, default=500)
    y = Column(Integer, default=500)
    size = Column(Integer, default=50)
    errors = Column(Integer, default=0)
    abs_speed = Column(Integer, default=2)
    speed_x = Column(Integer, default=2)
    speed_y = Column(Integer, default=2)
    color = Column(String(250), default="red")  # Добавили цвет
    w_vision = Column(Integer, default=800)
    h_vision = Column(Integer, default=600)  # Добавили размер

    def __init__(self, name, address):
        self.name = name
        self.address = address


Base.metadata.create_all(engine)


class LocalPlayer:
    def __init__(self, id, name, sock, addr):
        self.id = id
        self.db: Player = s.get(Player, self.id)
        self.sock = sock
        self.name = name
        self.address = addr
        self.x = 500
        self.y = 500
        self.size = 50
        self.errors = 0
        self.abs_speed = 2
        self.speed_x = 2
        self.speed_y = 2
        self.color = "red"
        self.w_vision = 800
        self.h_vision = 600

    def sync(self):
        self.db.size = self.size
        self.db.abs_speed = self.abs_speed
        self.db.speed_x = self.speed_x
        self.db.speed_y = self.speed_y
        self.db.errors = self.errors
        self.db.x = self.x
        self.db.y = self.y
        self.db.color = self.color
        self.db.w_vision = self.w_vision
        self.db.h_vision = self.h_vision
        s.merge(self.db)
        s.commit()

    def load(self):
        self.size = self.db.size
        self.abs_speed = self.db.abs_speed
        self.speed_x = self.db.speed_x
        self.speed_y = self.db.speed_y
        self.errors = self.db.errors
        self.x = self.db.x
        self.y = self.db.y
        self.color = self.db.color
        self.w_vision = self.db.w_vision
        self.h_vision = self.db.h_vision
        return self

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y

    def change_speed(self, vector):
        vector = filter2(vector)
        if vector == (0, 0):
            self.speed_x = self.speed_y = 0
        vector = vector[0] * self.abs_speed, vector[1] * self.abs_speed
        self.speed_x = vector[0]
        self.speed_y = vector[1]


server_works = True
while server_works:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            server_works = False
    screen.fill("blue")
    for id in players:
        player = players[id]
        x = player.x * WIDTH_SERVER // WIDTH_ROOM
        y = player.y * HEIGHT_SERVER // HEIGHT_ROOM
        size = player.size * WIDTH_SERVER // WIDTH_ROOM
        pygame.draw.circle(screen, player.color, (x, y), size)
    pygame.display.update()

    try:
        # проверяем желающих войти в игру
        new_socket, addr = main_socket.accept()  # принимаем входящие
        print('Подключился', addr)
        new_socket.setblocking(False)
        login = new_socket.recv(1024).decode()
        if login.startswith("color"):
            data = find_color(login[6:])
        player = Player("kj[", addr)
        player.name, player.color = data
        s.merge(player)
        s.commit()
        addr = f'({addr[0]},{addr[1]})'
        data = s.query(Player).filter(Player.address == addr)
        for user in data:
            player = LocalPlayer(user.id, "Имя", new_socket, addr)
            players[user.id] = player
    except BlockingIOError:
        pass

    # чтение информиции от игроков
    for id in list(players):
        try:
            data = players[id].sock.recv(1024).decode()
            print("---", data)
            players[id].change_speed(data)
        except:
            pass


    # движение игроков
    for id in list(players):
        players[id].update()

    # Обнаружение игроков
    visible_bacteries = {}
    for id in list(players):
        visible_bacteries[id] = []
    pairs = list(players.items())
    for i in range(0, len(pairs)):
        for j in range(i + 1, len(pairs)):
            # просматриваем пару игроков
            hero_1: LocalPlayer = pairs[i][1]
            hero_2: LocalPlayer = pairs[j][1]
            dist_x = hero_2.x - hero_1.x
            dist_y = hero_2.y - hero_1.y

            # i-й игрок видит j-того
            if abs(dist_x) <= hero_1.w_vision // 2 + hero_2.size and abs(dist_y) <= hero_1.h_vision // 2 + hero_2.size:
                x_ = str(round(dist_x))
                y_ = str(round(dist_y))
                size_ = str(round(hero_2.size))
                color_ = hero_2.color
                data = x_ + " " + y_ + " " + size_ + " " + color_
                visible_bacteries[hero_1.id].append(data)
            # j-тый игрок видит i-того
            if abs(dist_x) <= hero_2.w_vision // 2 + hero_1.size and abs(dist_y) <= hero_2.h_vision // 2 + hero_1.size:
                x_ = str(round(-dist_x))
                y_ = str(round(-dist_y))
                size_ = str(round(hero_1.size))
                color_ = hero_2.color
                data = x_ + " " + y_ + " " + size_ + " " + color_
                visible_bacteries[hero_2.id].append(data)

    # формируем ответ каждой бактырии
    for id in list(players):
        visible_bacteries[id] = "<"+",".join(visible_bacteries[id])+">"


    # Отправка игрокам поля
    for id in list(players):
        try:
            players[id].sock.send(visible_bacteries[id].encode())
        except:
            players[id].sock.close()
            del players[id]
            s.query(Player).filter(Player.id == id).delete()
            s.commit()
            print("Сокет закрыт")
pygame.quit()
main_socket.close()
s.query(Player).delete()
s.commit()
