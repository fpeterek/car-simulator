
class Wheel:

    def __init__(self):
        self.rotation = 0.0
        self.deg_per_second = 5.0
        self.max_rotation = 20.0

        self.target_rotation = 0.0

    @property
    def has_target(self):
        return self.target_rotation != 0.0

    def set_target(self, target, direction):
        target = min(target, self.max_rotation)
        self.target_rotation = target * int(direction)

    def unset_target(self):
        self.target_rotation = 0.0

    def bound_rotation(self):
        self.rotation = max(-self.max_rotation, self.rotation)
        self.rotation = min(self.max_rotation, self.rotation)

    def steer(self, dt):
        delta = self.deg_per_second * dt

        if self.rotation < self.target_rotation:
            if self.rotation + delta > self.target_rotation:
                self.rotation = self.target_rotation
            else:
                self.rotation += delta
        else:
            if self.rotation - delta < self.target_rotation:
                self.rotation = self.target_rotation
            else:
                self.rotation -= delta

        self.bound_rotation()

    def update(self, dt):
        self.steer(dt)
