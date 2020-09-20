import math
from typing import Tuple

from direction import Direction
from wheel import Wheel
from vector import Vector


class Car:

    default_weight = 1800  # kg
    default_top_speed = 230  # km/h
    default_brake_force = 15
    default_acceleration = 30
    default_deceleration = 0.05

    def __init__(self, x, y):

        self.x = x
        self.y = y

        self._velocity = 0.0
        self._rotation = 0.0

        self.target_velocity = -1

        self.front_wheel = Wheel()

        self.weight = Car.default_weight
        self.acceleration = Car.default_acceleration
        self.deceleration = Car.default_deceleration
        self.brake_force = Car.default_brake_force
        self.top_speed = Car.default_top_speed

    @property
    def position(self) -> Tuple[float, float]:
        return self.x, self.y

    @property
    def steering(self):
        return self.front_wheel.rotation

    @property
    def rotation(self):
        return math.radians(self._rotation)

    @property
    def forces(self):
        rotation = self.rotation
        fx = self._velocity * math.cos(rotation)
        fy = self._velocity * math.sin(rotation)

        return Vector(fx, fy)

    @property
    def velocity(self):
        return self._velocity

    @property
    def should_acc(self):
        return self._velocity < self.target_velocity

    @property
    def should_brake(self):
        return self.target_velocity == 0 or self._velocity > self.target_velocity + 3

    def drive(self, target_v, target_s):
        self.target_velocity = target_v
        direction = Direction.LEFT if target_s < 0 else Direction.RIGHT
        self.steer_target(abs(target_s), direction)

    def full_speed(self):
        self._velocity = self.top_speed

    def inverse_acc(self):
        return -2.94118 * (1 - math.e**(0.0112642 * self.velocity))

    def acc_fun(self, dt):
        t = self.inverse_acc() + dt
        return 88.777 * math.log(0.34 * (t+2.94118))

    def _acc(self, dt):
        new = self.acc_fun(dt)

        if new > self.target_velocity:
            self._velocity = self.target_velocity
        else:
            self._velocity = min(float(self.top_speed), new)

    def _dec(self, dt):
        delta = dt * max(self.deceleration * ((self._velocity / 10) ** 2), 1)

        if self._velocity-delta < self.target_velocity:
            self._velocity = self.target_velocity
        else:
            self._velocity -= delta

        self._velocity = max(self._velocity, 0)

    def _brake(self, dt):
        delta = dt * self.brake_force

        if self._velocity - delta > self.target_velocity:
            self._velocity -= dt * self.brake_force
        else:
            self._velocity = self.target_velocity

        self._velocity = max(self._velocity, 0)

    def calc_velocity(self, dt):
        if self.should_acc:
            self._acc(dt)
        else:
            self._dec(dt)
            if self.should_brake:
                self._brake(dt)

    def bound_rotation(self):
        if self._rotation > 360:
            self._rotation -= 360
        elif self._rotation < 0:
            self._rotation += 360

    def rotate(self, dt, wheel):
        self._rotation += wheel * dt * (self._velocity / self.top_speed * 4)
        self.bound_rotation()

    def steer_target(self, deg, direction):
        self.front_wheel.set_target(deg, direction)

    def unset_steer_target(self):
        self.front_wheel.unset_target()

    def move(self, dt):
        f = self.forces
        dx = f.x * dt
        dy = f.y * dt
        self.x += dx
        self.y += dy

    def update(self, dt):
        self.front_wheel.update(dt)
        self.rotate(dt, self.front_wheel.rotation)
        self.calc_velocity(dt)
        self.move(dt)
