import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Настраиваем сокет
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Отключаем пакетирование
sock.connect(("localhost", 11000))

while True:
    sock.send("И постепенно в усыпленье"
              "И чувств и дум впадает он,"
              "А перед ним воображенье"
              "Свой пестрый мечет фараон."
              "То видит он: на талом снеге,"
              "Как будто спящий на ночлеге,"
              "Недвижим юноша лежит,"
              "И слышит голос: что ж? убит."
              "То видит он врагов забвенных,"
              "Клеветников, и трусов злых,"
              "И рой изменниц молодых,"
              "И круг товарищей презренных,"
              "То сельский дом — и у окна"
              "Сидит она… и все она!..".encode())