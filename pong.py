from math import asin, tan
import pygame as pg
from pygame.locals import *
from random import randint
import pandas as pd
from sklearn.neighbors import KNeighborsRegressor

# Variables
WIDTH, HEIGHT = 1350, 650
BORDER = 5

fg_colour = pg.Color("pink")
bg_colour = pg.Color("black")
ball_colour = pg.Color("green")
paddle_colour = pg.Color("pink")

msg_colour = pg.Color("red")
msg_size = 150

velocity = [15, randint(-8, 8)]

# Classes
class Ball():
    radius = 10

    def __init__(self, position, velocity):
        self.position = position
        self.velocity = velocity

    def show(self, colour):
        global screen
        pg.draw.circle(screen, colour, self.position, self.radius)

    def update(self):
        global bg_colour, ball_colour, score
        newx = self.position[0] + self.velocity[0]
        newy = self.position[1] + self.velocity[1]

        if self.velocity[0] < 0 and newx < Paddle.width*2 + self.radius and newy > ai_paddle.y and newy < ai_paddle.y + Paddle.height:
            self.velocity[0] *= -1
            ball_pos = (self.position[1] - ai_paddle.y) / Paddle.height  # Location of ball on paddle, top of paddle = 0, bottom of paddle = 1

            # Make sure ball is touching paddle to prevent math error from tan(x<0) or tan(x>1)
            if ball_pos < 0:
                ball_pos = 0
            elif ball_pos > 1:
                ball_pos = 1

            # Ball reflects off paddle at an angle proportional to its position on the paddle
            angle_of_reflection = asin(ball_pos * 2 - 1) * 0.5
            self.velocity[1] = self.velocity[0] * tan(angle_of_reflection)
        elif self.velocity[0] > 0 and newx > WIDTH - Paddle.width*2 - self.radius and newy > human_paddle.y and newy < human_paddle.y + Paddle.height:
            self.velocity[0] *= -1
            ball_pos = (self.position[1] - human_paddle.y) / Paddle.height  # Location of ball on paddle, top of paddle = 0, bottom of paddle = 1

            # Make sure ball is touching paddle to prevent math error from tan(x<0) or tan(x>1)
            if ball_pos < 0:
                ball_pos = 0
            elif ball_pos > 1:
                ball_pos = 1

            # Ball reflects off paddle at an angle proportional to its position on the paddle
            angle_of_reflection = -asin(ball_pos * 2 - 1) * 0.5
            self.velocity[1] = self.velocity[0] * tan(angle_of_reflection)
        elif newy < BORDER + self.radius or newy > HEIGHT - BORDER - self.radius:
            self.velocity[1] *= -1
        else:
            self.show(bg_colour)
            self.position[0] += self.velocity[0]
            self.position[1] += self.velocity[1]
            self.show(ball_colour)

class Paddle():
    height = 150
    width = 15

    def __init__(self, y):
        self.y = y

    def show(self, x, colour):
        global screen
        pg.draw.rect(screen, colour, pg.Rect(x, self.y, self.width, self.height))

    def update(self):
        global bg_colour, paddle_colour
        mouse_pos = pg.mouse.get_pos()[1]
        self.show(WIDTH - self.width*2, bg_colour)

        if mouse_pos < BORDER + self.height // 2:
            self.y = BORDER
        elif mouse_pos > HEIGHT - BORDER - self.height // 2:
            self.y = HEIGHT - BORDER - self.height
        else:
            self.y = mouse_pos - self.height // 2

        self.show(WIDTH - self.width*2, paddle_colour)

    def ai_update(self, prediction):
        global bg_colour, paddle_colour
        self.show(self.width, bg_colour)

        if prediction < BORDER + self.height // 2:
            self.y = BORDER
        elif prediction > HEIGHT - BORDER - self.height // 2:
            self.y = HEIGHT - BORDER - self.height
        else:
            self.y = prediction - self.height // 2

        self.show(self.width, paddle_colour)

# Initialise screen
pg.init()
screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("Pong")

# Draw border
pg.draw.rect(screen, fg_colour, pg.Rect(0, 0, WIDTH, BORDER))
pg.draw.rect(screen, fg_colour, pg.Rect(0, HEIGHT - BORDER, WIDTH, BORDER))

# Create ball and paddle instances
ball = Ball([WIDTH//2, HEIGHT//2], velocity)
ai_paddle = Paddle(HEIGHT//2 - Paddle.height//2)
human_paddle = Paddle(HEIGHT//2 - Paddle.height//2)

#game_data = open("game_data.csv", "a")
#print("x,y,vx,vy,paddle.y", file=game_data)

pong = pd.read_csv("game_data.csv").dropna()

X = pong.drop(columns="paddle.y")
y = pong["paddle.y"]

clf = KNeighborsRegressor(n_neighbors=3)
clf.fit(X, y)

df = pd.DataFrame(columns=["x", "y", "vx", "vy"])

def main():
    # Show ball and paddle
    ball.show(ball_colour)
    ai_paddle.show(Paddle.width, paddle_colour)
    human_paddle.show(WIDTH - Paddle.width*2, paddle_colour)

    # Display message if game finishes
    msg_font = pg.font.SysFont(None, msg_size)
    msg_surface = msg_font.render("GAME OVER", False, msg_colour)

    # Initialise clock
    clock = pg.time.Clock()

    # Event loop
    while True:
        # Make sure game doesn't run at more than 60 frames per second
        clock.tick(60)

        # Check for quit event
        event = pg.event.poll()
        if event.type == QUIT:
            return

        pg.display.flip()

        if ball.position[0] < 0 or ball.position[0] > WIDTH:
            screen.blit(msg_surface, (WIDTH // 2 - msg_surface.get_width() // 2, HEIGHT // 2 - msg_surface.get_height())) #  Blit message to screen if game finishes
            pg.display.flip()
            pg.time.wait(2000)
            return
        else:
            to_predict = df.append({"x": ball.position[0], "y": ball.position[1], "vx": ball.velocity[0], "vy": ball.velocity[1]}, ignore_index=True)
            should_move = clf.predict(to_predict)[0]
            ai_paddle.ai_update(should_move)
            human_paddle.update()
            ball.update()
            #print(f"{ball.position[0]},{ball.position[1]},{ball.velocity[0]},{ball.velocity[1]},{paddle.y}", file=game_data)

main()
pg.quit()