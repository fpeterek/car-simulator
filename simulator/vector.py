from typing import Union


class Vector:

    def __init__(self, x: Union[int, float] = None, y: Union[int, float] = None):
        if x is None:
            self.x = 0
            self.y = 0
        elif y is None:
            self.x = x
            self.y = x
        else:
            self.x = x
            self.y = y

    def __str__(self):
        return f'({self.x}, {self.y})'
