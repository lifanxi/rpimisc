#! /usr/bin/python
import sys
import time
from enum import Enum
from random import randint
from sense_hat import SenseHat
from evdev import InputDevice, list_devices, ecodes

class Key(Enum):
    KEY_RIGHT = 1
    KEY_LEFT = 2
    KEY_UP = 3
    KEY_DOWN = 4
    
class SnakeGame:
    def __init__(self):
        self.snake = [[3, 3]]
        self.food = [3,2]
        self.score = 0
        self.last = [3,3]
        self.key = Key.KEY_RIGHT
    def next(self):
        self.snake.insert(0, [self.snake[0][0] + (self.key == Key.KEY_RIGHT and 1) + (self.key == Key.KEY_LEFT and -1), self.snake[0][1] + (self.key == Key.KEY_UP and -1) + (self.key == Key.KEY_DOWN and 1)])
        if self.snake[0][0] == -1:
            self.snake[0][0] = 7
        if self.snake[0][1] == -1:
            self.snake[0][1] = 7
        if self.snake[0][0] == 8:
            self.snake[0][0] = 0
        if self.snake[0][1] == 8:
            self.snake[0][1] = 0
        if self.snake[0] in self.snake[1:]:
            return False
        if self.snake[0] == self.food:                                            # When snake eats the food
            self.food = []
            self.score += 1
            while self.food == []:
                self.food = [randint(0, 7), randint(0, 7)]                 # Calculating next food's coordinates
                if self.food in self.snake:
                    self.food = []
        else:
            self.last = self.snake.pop()     
        return True
    def up(self):
        self.key = Key.KEY_UP
    def down(self):
        self.key = Key.KEY_DOWN
    def left(self):
        self.key = Key.KEY_LEFT
    def right(self):
        self.key = Key.KEY_RIGHT
    def show(self):
        for i in self.snake:
            sense.set_pixel(i[0], i[1], 255,255,255)
        if self.last != None:
            sense.set_pixel(self.last[0], self.last[1], 0,0,0)
        if self.food != None:
            sense.set_pixel(self.food[0], self.food[1], 255,0,0)
        print(self.snake)
    def game_over(self):
        sense.show_message("Game Over!")
        sense.show_message("Score: %s" % self.score)
    def get_score(self):
        return self.score
            
        
if __name__ == '__main__':
    sense = SenseHat()
    sense.clear()  # Blank the LED matrix
    sense.low_light = False
    found = False;
    devices = [InputDevice(fn) for fn in list_devices()]
    for dev in devices:
        if dev.name == 'Raspberry Pi Sense HAT Joystick':
            found = True;
            break

    if not(found):
        print('Raspberry Pi Sense HAT Joystick not found. Aborting ...')
        sys.exit()

    s = SnakeGame()
    last_code = None
    last_ts = time.time()
    try:
        while True:
            event = dev.read_one()
            if event == None:
                if (time.time() - last_ts) * 1000 < 800 / (s.get_score() / 3 + 1):
                    continue
                else:
                    last_ts = time.time()
            else:
                if event.type == 0:
                    continue
                if event.type == ecodes.EV_KEY:
                        print event.code
                        print last_code
                        if event.code == last_code:
                            print "."
                            continue
                        else:
                            last_code = event.code
                        if event.value == 1:  # key down
                            if event.code == ecodes.KEY_DOWN:
                                s.down()
                            if event.code == ecodes.KEY_UP:
                                s.up()
                            if event.code == ecodes.KEY_LEFT:
                                s.left()
                            if event.code == ecodes.KEY_RIGHT:
                                s.right()
            if not s.next():
                s.game_over()
                s = SnakeGame()
                last_code = None
                last_ts = time.time()
                continue
            s.show()
            last_ts = time.time()
    except KeyboardInterrupt:
        sense.clear()  # Blank the LED matrix
        sys.exit()

        
            
