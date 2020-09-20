import socketserver
import os
import time
import math
from typing import Tuple
from threading import Lock, Thread

from car import Car

debug = os.getenv('SOCKET_DEBUG') and os.getenv('SOCKET_DEBUG').lower() in ('true', '1')


class Server:

    car: Car = Car(0, 0)
    car_lock: Lock = Lock()
    car_thread: Thread = None

    cont = True
    cont_lock: Lock = Lock()

    start_lat = float(os.getenv('START_LAT'))
    start_lon = float(os.getenv('START_LON'))

    @staticmethod
    def to_lonlat(x: float, y: float) -> Tuple[float, float]:
        x /= 100
        y /= 100
        new_lat = Server.start_lat + y / 6_378_000 * 180 / math.pi
        new_lon = Server.start_lon + (x / 6_378_000 * 180 / math.pi) / math.cos(math.radians(Server.start_lat))
        return new_lat, new_lon

    class Handler(socketserver.BaseRequestHandler):

        def drive(self, v, s):
            if debug:
                print(f'Received (v, s) = ({v}, {s})')

            if Server.car is not None:
                Server.car.drive(v, s)

            self.healthcheck()

        def healthcheck(self):
            if debug:
                print('Healthcheck (status=Alive)')

            status = 1
            self.request.sendall(status.to_bytes(1, 'little'))

        def info(self):

            v = Server.car.velocity if Server.car is not None else 0
            s = Server.car.steering if Server.car is not None else 0
            b = 0
            if debug:
                print(f'Driving data (v, s) = ({v}, {s})')

            v = v.to_bytes(1, 'little', signed=True)
            s = s.to_bytes(1, 'little', signed=True)
            b = b.to_bytes(1, 'little', signed=True)
            self.request.sendall(v + s + b)

        def ebrake(self, brake: bool):
            if debug:
                print(f'Emergency brake {["unimplemented", "unimplemented"][int(brake)]}')

            self.healthcheck()

        def position(self):
            if debug:
                print('Position')
            ok = 0
            try:
                x, y = Server.car.position
                print(f'Car pos: {Server.car.position}, v={Server.car.velocity}')
                ok = 1
            except:
                x, y = 0, 0
            x, y = Server.to_lonlat(x, y)
            print('x:', x, 'y:', y, 'ok:', ok)
            x = int(x * 10000000000)
            y = int(y * 10000000000)
            ok = ok.to_bytes(1, 'little', signed=False)
            x = x.to_bytes(8, 'little', signed=True)
            y = y.to_bytes(8, 'little', signed=True)

            self.request.sendall(ok + x + y)

        def handle_request(self):
            data = self.request.recv(3)
            message_type = int.from_bytes(data[0:1], 'little', signed=False)
            b1 = int.from_bytes(data[1:2], 'little', signed=True)
            b2 = int.from_bytes(data[2:3], 'little', signed=True)

            if message_type == 0:
                self.drive(v=b1, s=b2)
            elif message_type == 1:
                self.healthcheck()
            elif message_type == 2:
                self.info()
            elif message_type == 3:
                self.ebrake(brake=bool(b1))
            elif message_type == 4:
                self.position()

        def handle(self):
            try:
                Server.car_lock.acquire()
                self.handle_request()
            finally:
                Server.car_lock.release()

    @staticmethod
    def car_loop():
        last = time.time_ns()
        dt = 0
        while True:
            try:
                Server.car_lock.acquire()
                Server.car.update(dt=dt)

                current = time.time_ns()
                dt = (current - last) / 10 ** 9
                last = current
            finally:
                Server.car_lock.release()
            try:
                Server.cont_lock.acquire()
                if not Server.cont:
                    break
            finally:
                Server.cont_lock.release()
            time.sleep(0.01)

    @staticmethod
    def serve(host: str = None, port: int = None):

        if not host:
            host = os.getenv("SERVER_HOST")
        if port is None or port < 0:
            port = int(os.getenv("SERVER_PORT"))

        with socketserver.TCPServer((host, port), Server.Handler) as server:
            print('Starting server...')
            try:
                Server.car_thread = Thread(target=Server.car_loop)
                Server.car_thread.start()
                server.serve_forever()
            finally:
                Server.cont_lock.acquire()
                Server.cont = False
                Server.cont_lock.release()
                Server.car_thread.join(0.5)
                server.server_close()

