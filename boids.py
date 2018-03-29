import random
from tkinter import *

windowWidth = 800
windowHeight = 800
boidCount = 40
wallForceDepth = 100
wallForce = 2
maxVelocity = 50
boidRadius = 3

def main():
    initialise()
    # mainloop begins at update()
    mainloop()

def initialise():
    global boids
    global scatterTime
    global windTime
    global foodTime
    scatterTime = 0
    windTime = 0
    foodTime = 0
    boids = []
    for i in range(boidCount):
        boids.append(Boid())
    build_graph()

def build_graph():
    global graph
    root = Tk()
    root.overrideredirect(True)
    root.geometry('%dx%d+%d+%d' % (windowWidth, windowHeight, (root.winfo_screenwidth() - windowWidth) / 2, (root.winfo_screenheight() - windowHeight) / 2))
    root.bind_all('<Escape>', lambda event: event.widget.quit())
    graph = Canvas(root, width=windowWidth, height=windowHeight, background='white')
    graph.after(40, update)
    graph.pack()

def update():
    draw()
    moveBoids()
    graph.after(20, update)

def draw():
    graph.delete(ALL)
    for boid in boids:
        x1 = boid.position.x - boidRadius
        y1 = boid.position.y - boidRadius
        x2 = boid.position.x + boidRadius
        y2 = boid.position.y + boidRadius

        graph.create_rectangle((x1, y1, x2, y2), fill='black')
    graph.update()

def moveBoids():
    global scatterTime
    global windTime
    global foodTime
    if scatterTime == 0:
        scatterChance = random.randint(1, 1000)
        if scatterChance <= 1:
            scatterTime = random.randint(750, 1000)
    if windTime == 0:
        windChance = random.randint(1, 1000)
        if windChance <= 1:
            windTime = random.randint(750, 1000)
    if foodTime == 0:
        foodChance = random.randint(1, 1000)
        if foodChance <= 1:
            foodTime = random.randint(5000, 10000)
    for boid in boids:
        if scatterTime != 0:
            print("scattering")
            if windTime != 0:
                print("wind blowing")
                boid.movement(True, True, False)
                windTime -= 1
            else:
                boid.movement(True, False, False)
            scatterTime -= 1
        else:
            if windTime != 0:
                print("wind blowing")
                boid.movement(False, True, False)
                windTime -= 1
            # Food only enticing when not scared or windy
            else:
                if foodTime != 0:
                    print("food here")
                    boid.movement(False, False, True)
                    foodTime -= 1
                else:
                    boid.movement(False, False, False)
        contain(boid)

def contain(boid):
    if boid.position.x < wallForceDepth:
        boid.velocity.x += wallForce
    elif boid.position.x > windowWidth - wallForceDepth:
        boid.velocity.x -= wallForce
    if boid.position.y < wallForceDepth:
        boid.velocity.y += wallForce
    elif boid.position.y > windowHeight - wallForceDepth:
        boid.velocity.y -= wallForce

class TwoD:

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def __add__(self, other):
        return TwoD(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return TwoD(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return TwoD(self.x * other, self.y * other)

    def __truediv__(self, other):
        return TwoD(self.x / other, self.y / other)

    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        return self

    def __isub__(self, other):
        self.x -= other.x
        self.y -= other.y
        return self

    def __itruediv__(self, other):
        if other:
            self.x /= other
        if other:
            self.y /= other
        return self

    def magnitude(self):
        return ((self.x ** 2) + (self.y ** 2)) ** 0.5

class Boid:

    def __init__(self):
        initialVelocityX = random.randint(-1*maxVelocity, maxVelocity)
        initialVelocityY = random.randint(-1*maxVelocity, maxVelocity)
        self.velocity = TwoD(initialVelocityX, initialVelocityY)

        initialPositionX = random.randint(0, windowWidth)
        initialPositionY = random.randint(0, windowHeight)
        self.position = TwoD(initialPositionX, initialPositionY)

        self.perchTime = random.randint(100, 400)
        self.perching = False

    def movement(self, scatterBool, windBool, foodBool):
        if scatterBool == True:
            s = -500
        else:
            s = 1
        if windBool == True:
            w = random.randint(1, 5)
        else:
            w = 0
        if foodBool == True:
            f = random.randint(1, 3)
        else:
            f = 0
        if self.perching == False:
            v1 = self.rule1() * s
            v2 = self.rule2()
            v3 = self.rule3()
            v4 = self.wind(windBool) * w
            v5 = self.food(foodBool) * f
            self.velocity += v1 + v2 + v3 + v4 + v5
            if self.velocity.magnitude() > maxVelocity:
                self.velocity /= self.velocity.magnitude() / maxVelocity
            perchChance = random.randint(1, 1000)
            if self.velocity.magnitude() < maxVelocity / 3.75 and perchChance < 6:
                self.perching = True
            else:
                self.position += self.velocity / 10
        else:
            if self.perchTime == 0:
                self.perching = False
                self.perchTime = random.randint(100, 400)
            else:
                self.perchTime -= 1

    # Flock Cohesion
    '''
    Determines average position of all boids, returns 5% of the resulting vector
    so that each boid moves 5% toward the center mass of the flock on each iteration.
    '''
    def rule1(self):
        boidsActive = 0
        vector = TwoD(0, 0)
        for boid in boids:
            if boid is not self and boid.perching == False:
                vector += boid.position
                boidsActive += 1
        vector /= boidsActive
        return (vector - self.position) / 100

    # Separation
    '''
    If the boid is too close to another boid in the flock, return the negative vector displacement
    of the boid and the other boid. This makes it so that the boid tends to stay away from its
    neighbors.
    '''
    def rule2(self):
        vector = TwoD(0, 0)
        for boid in boids:
            if boid is not self and boid.perching == False:
                if (boid.position - self.position).magnitude() < 6*boidRadius:
                    vector -= (boid.position - self.position) / 10
        return vector

    # Alignment
    '''
    Takes the average velocities of the other boids, this is the perceived velocity of the flock.
    returns a velocity equal to 4% of the perceived velocity of the flock so that the boid tends
    to move in the same direction as the flock.
    '''
    def rule3(self):
        boidsActive = 0
        vector = TwoD(0, 0)
        for boid in boids:
            if boid is not self and boid.perching == False:
                vector += boid.velocity
                boidsActive += 1
        vector /= boidsActive
        return (vector - self.velocity) / 25

    # Wind
    '''
    Returns a constant vector, representing a wind force which is applied to all boids equally.
    '''
    def wind(self, windBool):
        if windBool:
            graph.create_rectangle((windowWidth / 2 - 10, windowHeight / 2 - 1, windowWidth / 2 + 10, windowHeight / 2 + 1), fill='red')
        windVector = TwoD(1, 0)
        return windVector

    # Food
    '''
    Places a food morcel in the middle of the window, represented by a vector force in that
    direction.
    '''
    def food(self, foodBool):
        if foodBool:
            graph.create_rectangle((windowWidth / 2 - boidRadius, windowHeight / 2 - boidRadius, windowWidth / 2 + boidRadius, windowHeight / 2 + boidRadius), fill='red')
        foodVector = TwoD(windowWidth / 2, windowHeight / 2)
        return (foodVector - self.position) / 5

main()
