import random

import pygame
from pygame.locals import *

from Pacman_Complete.vector import Vector2
from entity import Entity
from constants import *
from pacman import Pacman
from nodes import NodeGroup
from pellets import PelletGroup
from ghosts import GhostGroup
from fruit import Fruit
from pauser import Pause
from text import TextGroup
from sprites import LifeSprites
from sprites import MazeSprites
from mazedata import MazeData


class GameController(object):
    def __init__(self):
        self.have_ghost = False
        self.current_node = Vector2()
        pygame.init()
        self.screen = pygame.display.set_mode(SCREENSIZE, 0, 32)
        self.background = None
        self.background_norm = None
        self.background_flash = None
        self.clock = pygame.time.Clock()
        self.fruit = None
        self.pause = Pause(True)
        self.level = 0
        self.lives = 5
        self.score = 0
        self.textgroup = TextGroup()
        self.lifesprites = LifeSprites(self.lives)
        self.flashBG = False
        self.flashTime = 0.2
        self.flashTimer = 0
        self.fruitCaptured = []
        self.fruitNode = None
        self.mazedata = MazeData()

    def setBackground(self):
        self.background_norm = pygame.surface.Surface(SCREENSIZE).convert()
        self.background_norm.fill(BLACK)
        self.background_flash = pygame.surface.Surface(SCREENSIZE).convert()
        self.background_flash.fill(BLACK)
        self.background_norm = self.mazesprites.constructBackground(self.background_norm, self.level % 5)
        self.background_flash = self.mazesprites.constructBackground(self.background_flash, 5)
        self.flashBG = False
        self.background = self.background_norm

    def startGame(self):
        self.mazedata.loadMaze(self.level)
        self.mazesprites = MazeSprites(self.mazedata.obj.name + ".txt", self.mazedata.obj.name + "_rotation.txt")
        self.setBackground()
        self.nodes = NodeGroup(self.mazedata.obj.name + ".txt")
        self.mazedata.obj.setPortalPairs(self.nodes)
        self.mazedata.obj.connectHomeNodes(self.nodes)
        self.pacman = Pacman(self.nodes.getNodeFromTiles(*self.mazedata.obj.pacmanStart))
        self.pellets = PelletGroup(self.mazedata.obj.name + ".txt")
        self.ghosts = GhostGroup(self.nodes.getStartTempNode(), self.pacman)

        self.ghosts.pinky.setStartNode(self.nodes.getNodeFromTiles(*self.mazedata.obj.addOffset(2, 3)))
        self.ghosts.inky.setStartNode(self.nodes.getNodeFromTiles(*self.mazedata.obj.addOffset(0, 3)))
        self.ghosts.clyde.setStartNode(self.nodes.getNodeFromTiles(*self.mazedata.obj.addOffset(4, 3)))
        self.ghosts.setSpawnNode(self.nodes.getNodeFromTiles(*self.mazedata.obj.addOffset(2, 3)))
        self.ghosts.blinky.setStartNode(self.nodes.getNodeFromTiles(*self.mazedata.obj.addOffset(2, 0)))

        self.nodes.denyHomeAccess(self.pacman)
        self.nodes.denyHomeAccessList(self.ghosts)
        self.ghosts.inky.startNode.denyAccess(RIGHT, self.ghosts.inky)
        self.ghosts.clyde.startNode.denyAccess(LEFT, self.ghosts.clyde)
        self.mazedata.obj.denyGhostsAccess(self.ghosts, self.nodes)

    def startGame_old(self):
        self.mazedata.loadMaze(self.level)  #######
        self.mazesprites = MazeSprites("maze1.txt", "maze1_rotation.txt")
        self.setBackground()
        self.nodes = NodeGroup("maze1.txt")
        self.nodes.setPortalPair((0, 17), (27, 17))
        homekey = self.nodes.createHomeNodes(11.5, 14)
        self.nodes.connectHomeNodes(homekey, (12, 14), LEFT)
        self.nodes.connectHomeNodes(homekey, (15, 14), RIGHT)
        self.pacman = Pacman(self.nodes.getNodeFromTiles(15, 26))
        self.pellets = PelletGroup("maze1.txt")
        self.ghosts = GhostGroup(self.nodes.getStartTempNode(), self.pacman)
        self.ghosts.blinky.setStartNode(self.nodes.getNodeFromTiles(2 + 11.5, 0 + 14))
        self.ghosts.pinky.setStartNode(self.nodes.getNodeFromTiles(2 + 11.5, 3 + 14))
        self.ghosts.inky.setStartNode(self.nodes.getNodeFromTiles(0 + 11.5, 3 + 14))
        self.ghosts.clyde.setStartNode(self.nodes.getNodeFromTiles(4 + 11.5, 3 + 14))
        self.ghosts.setSpawnNode(self.nodes.getNodeFromTiles(2 + 11.5, 3 + 14))

        self.nodes.denyHomeAccess(self.pacman)
        self.nodes.denyHomeAccessList(self.ghosts)
        self.nodes.denyAccessList(2 + 11.5, 3 + 14, LEFT, self.ghosts)
        self.nodes.denyAccessList(2 + 11.5, 3 + 14, RIGHT, self.ghosts)
        self.ghosts.inky.startNode.denyAccess(RIGHT, self.ghosts.inky)
        self.ghosts.clyde.startNode.denyAccess(LEFT, self.ghosts.clyde)
        self.nodes.denyAccessList(12, 14, UP, self.ghosts)
        self.nodes.denyAccessList(15, 14, UP, self.ghosts)
        self.nodes.denyAccessList(12, 26, UP, self.ghosts)
        self.nodes.denyAccessList(15, 26, UP, self.ghosts)

    def update(self):
        dt = self.clock.tick(30) / 1000.0
        self.textgroup.update(dt)
        self.pellets.update(dt)
        if not self.pause.paused:
            self.ghosts.update(dt)
            if self.fruit is not None:
                self.fruit.update(dt)
            self.checkPelletEvents()
            self.checkGhostEvents()
            self.checkFruitEvents()

        if self.pacman.alive:
            if not self.pause.paused:
                self.pacman.update(dt)
        else:
            self.pacman.update(dt)

        if self.flashBG:
            self.flashTimer += dt
            if self.flashTimer >= self.flashTime:
                self.flashTimer = 0
                if self.background == self.background_norm:
                    self.background = self.background_flash
                else:
                    self.background = self.background_norm

        afterPauseMethod = self.pause.update(dt)
        if afterPauseMethod is not None:
            afterPauseMethod()
        self.checkEvents()
        self.render()

        ######################################
        #                 IA                 #
        ######################################

        # Get pacman position
        pacman_X = self.pacman.node.position.x
        pacman_Y = self.pacman.node.position.y

        # Check if pacman position is a new node
        new_node = False
        if self.current_node != Vector2(pacman_X, pacman_Y):
            self.current_node = Vector2(pacman_X, pacman_Y)
            new_node = True

        # Get limits of current corridor
        max_X = 0
        min_X = 0
        max_Y = 0
        min_Y = 0

        for a in range(int(pacman_X), self.screen.get_width()):
            node = self.nodes.getNodeFromPixels(a, pacman_Y)
            if node is not None and node.neighbors[RIGHT] is None:
                max_X = node.position.x
                break
        for a in reversed(range(0, int(pacman_X) + 1)):
            node = self.nodes.getNodeFromPixels(a, pacman_Y)
            if node is not None and node.neighbors[LEFT] is None:
                min_X = node.position.x
                break
        for a in range(int(pacman_Y), self.screen.get_height()):
            node = self.nodes.getNodeFromPixels(pacman_X, a)
            if node is not None and node.neighbors[DOWN] is None:
                max_Y = node.position.y
                break
        for a in reversed(range(0, int(pacman_Y) + 1)):
            node = self.nodes.getNodeFromPixels(pacman_X, a)
            if node is not None and node.neighbors[UP] is None:
                min_Y = node.position.y
                break

        # Get all nodes that could be travelled

        nodes = self.nodes.nodesLUT
        nodes_X_all = []
        nodes_Y_all = []

        for node in nodes:
            if node[1] == pacman_Y:
                nodes_X_all.append(node)
            elif node[0] == pacman_X:
                nodes_Y_all.append(node)

        nodes_X = []
        nodes_Y = []
        for node in nodes_X_all:
            if min_X <= node[0] <= max_X:
                nodes_X.append(node)
        for node in nodes_Y_all:
            if min_Y <= node[1] <= max_Y:
                nodes_Y.append(node)

        # Set pacman position to be in the next node and check all possibilities
        # Because when pacman is between nodes is always checking th previous node

        if self.pacman.direction == LEFT and (pacman_X, pacman_Y) in nodes_X:
            index = nodes_X.index((pacman_X, pacman_Y))
            if len(nodes_X) > 1:
                next_node = nodes_X[index - 1]
                pacman_X = next_node[0]
        elif self.pacman.direction == RIGHT and (pacman_X, pacman_Y) in nodes_X:
            index = nodes_X.index((pacman_X, pacman_Y))
            if index + 1 < len(nodes_X):
                next_node = nodes_X[index + 1]
                pacman_X = next_node[0]
        elif self.pacman.direction == UP and (pacman_X, pacman_Y) in nodes_Y:
            index = nodes_Y.index((pacman_X, pacman_Y))
            if len(nodes_Y) > 1:
                next_node = nodes_Y[index - 1]
                pacman_Y = next_node[1]
        elif self.pacman.direction == DOWN and (pacman_X, pacman_Y) in nodes_Y:
            index = nodes_Y.index((pacman_X, pacman_Y))
            if index + 1 < len(nodes_Y):
                next_node = nodes_Y[index + 1]
                pacman_Y = next_node[1]

        # Get valid directions
        directions = Entity.validDirections(self.pacman)
        print(directions)

        # Array with ghosts
        ghosts_positions = []
        ghosts_positions.append(self.ghosts.inky)
        ghosts_positions.append(self.ghosts.blinky)
        ghosts_positions.append(self.ghosts.clyde)
        ghosts_positions.append(self.ghosts.pinky)
        # Vars to check where were found ghosts
        found_above = False
        found_bellow = False
        found_at_left = False
        found_at_right = False
        found_ghost_on_iteration = False

        # For each ghost check if ghost is between pacman and the wall, and the mode of the ghost
        for ghost in ghosts_positions:
            if ghost.node.position.x == pacman_X and min_Y <= ghost.node.position.y <= pacman_Y and ghost.mode != FREIGHT:
                found_above = True

            if ghost.node.position.x == pacman_X and max_Y >= ghost.node.position.y >= pacman_Y and ghost.mode != FREIGHT:
                found_bellow = True

            if min_X <= ghost.node.position.x <= pacman_X and ghost.node.position.y == pacman_Y and ghost.mode != FREIGHT:
                found_at_left = True

            if max_X >= ghost.node.position.x >= pacman_X and ghost.node.position.y == pacman_Y and ghost.mode != FREIGHT:
                found_at_right = True

        # Check if ghost was found in the run of update or was in a previous run
        if (found_above or found_bellow or found_at_left or found_at_right) and not self.have_ghost:
            found_ghost_on_iteration = True

        # Remove all the directions that contain ghosts
        if found_above or found_bellow or found_at_left or found_at_right:
            if found_above and UP in directions:
                directions.remove(UP)
                print("Found  ghost up")
            if found_bellow and DOWN in directions:
                directions.remove(DOWN)
                print("Found  ghost down")
            if found_at_left and LEFT in directions:
                directions.remove(LEFT)
                print("Found  ghost left")
            if found_at_right and RIGHT in directions:
                directions.remove(RIGHT)
                print("Found  ghost right")
            self.have_ghost = True

        # check if still having ghost in the corridor
        if self.have_ghost and not (found_above or found_bellow or found_at_left or found_at_right):
            self.have_ghost = False

        # Calculate the number os pellets in each corridor
        left = 0
        right = 0
        top = 0
        bottom = 0
        for p in self.pellets.pelletList:
            if p.position.y == pacman_Y and pacman_X >= p.position.x >= min_X:
                left += 1
            elif p.position.y == pacman_Y and pacman_X <= p.position.x <= max_X:
                right += 1
            elif p.position.x == pacman_X and pacman_Y >= p.position.y >= min_Y:
                top += 1
            elif p.position.x == pacman_X and pacman_Y <= p.position.y <= max_Y:
                bottom += 1

        # Create new dictionary withs values and keys
        dict_of_values = {"left": left, "right": right, "top": top, "bottom": bottom}
        # Sort dictionary
        dict_of_values = {k: v for k, v in sorted(dict_of_values.items(), key=lambda item: item[0])}

        # remove not valid directions
        if not LEFT in directions:
            dict_of_values.pop("left")
        if not RIGHT in directions:
            dict_of_values.pop("right")
        if not UP in directions:
            dict_of_values.pop("top")
        if not DOWN in directions:
            dict_of_values.pop("bottom")
        print(dict_of_values)
        # Calculate next direction

        if found_ghost_on_iteration:
            if len(directions) != 0:
                # Select a random direction just to run away from ghost
                next_direction = random.choice(directions)
            else:
                # Maintain the direction, because no other were available
                next_direction = self.pacman.direction
        elif not self.have_ghost:
            # Mean that the corridors were clear, and choose the direction with most pellets
            next_direction = max(dict_of_values, key=dict_of_values.get)
        else:
            next_direction = self.pacman.direction
        print(next_direction)

        # Define var of pacman to help to choose paths in directionMethod
        if len(directions) != 0:
            self.pacman.valid_directions = directions
        else:
            self.pacman.valid_directions = [self.pacman.direction]

        # Check if found some ghosts and escape from that directions
        if self.have_ghost:
            if next_direction == 2:
                self.pacman.escape(LEFT)
            elif next_direction == -2:
                self.pacman.escape(RIGHT)
            elif next_direction == 1:
                self.pacman.escape(UP)
            elif next_direction == -1:
                self.pacman.escape(DOWN)
        # Mean that tha fruit was dropped, and we can catch
        # Define goal equal to fruit.position
        # Only came here, if the corridors were clear
        elif self.fruit is not None:
            self.pacman.goal = Vector2(self.fruit.position.x, self.fruit.position.y)
            self.pacman.directionMethod = self.pacman.goalDirection
        # No fruit or ghosts were found, so check the direction with more pellets
        elif new_node:
            if next_direction == "left" or next_direction == 2:
                # Define the goal as the left limit of the corridor
                self.pacman.goal = Vector2(min_X, pacman_Y)
            elif next_direction == "right" or next_direction == -2:
                # Define the goal as the right limit of the corridor
                self.pacman.goal = Vector2(max_X, pacman_Y)
            elif next_direction == "top" or next_direction == 1:
                # Define the goal as the top limit of the corridor
                self.pacman.goal = Vector2(pacman_X, min_Y)
            elif next_direction == "bottom" or next_direction == -1:
                # Define the goal as the bottom limit of the corridor
                self.pacman.goal = Vector2(pacman_X, max_Y)
            if len(directions) != 0:
                # Set direction Method equal to goalDirection function
                self.pacman.directionMethod = self.pacman.goalDirection

    ######################################
    #                 IA                 #
    ######################################

    def checkEvents(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                exit()
            elif event.type == KEYDOWN:
                if event.key == K_SPACE:
                    if self.pacman.alive:
                        self.pause.setPause(playerPaused=True)
                        if not self.pause.paused:
                            self.textgroup.hideText()
                            self.showEntities()
                        else:
                            self.textgroup.showText(PAUSETXT)
                            # self.hideEntities()

    def checkPelletEvents(self):
        pellet = self.pacman.eatPellets(self.pellets.pelletList)
        if pellet:
            self.pellets.numEaten += 1
            self.updateScore(pellet.points)
            if self.pellets.numEaten == 30:
                self.ghosts.inky.startNode.allowAccess(RIGHT, self.ghosts.inky)
            if self.pellets.numEaten == 70:
                self.ghosts.clyde.startNode.allowAccess(LEFT, self.ghosts.clyde)
            self.pellets.pelletList.remove(pellet)
            if pellet.name == POWERPELLET:
                self.ghosts.startFreight()
            if self.pellets.isEmpty():
                self.flashBG = True
                self.hideEntities()
                self.pause.setPause(pauseTime=3, func=self.nextLevel)

    def checkGhostEvents(self):
        for ghost in self.ghosts:
            if self.pacman.collideGhost(ghost):
                if ghost.mode.current is FREIGHT:
                    self.pacman.visible = False
                    ghost.visible = False
                    self.updateScore(ghost.points)
                    self.textgroup.addText(str(ghost.points), WHITE, ghost.position.x, ghost.position.y, 8, time=1)
                    self.ghosts.updatePoints()
                    self.pause.setPause(pauseTime=1, func=self.showEntities)
                    ghost.startSpawn()
                    self.nodes.allowHomeAccess(ghost)
                elif ghost.mode.current is not SPAWN:
                    if self.pacman.alive:
                        self.lives -= 1
                        self.lifesprites.removeImage()
                        self.pacman.die()
                        self.ghosts.hide()
                        if self.lives <= 0:
                            self.textgroup.showText(GAMEOVERTXT)
                            self.pause.setPause(pauseTime=3, func=self.restartGame)
                        else:
                            self.pause.setPause(pauseTime=3, func=self.resetLevel)

    def checkFruitEvents(self):
        if self.pellets.numEaten == 50 or self.pellets.numEaten == 140:
            if self.fruit is None:
                self.fruit = Fruit(self.nodes.getNodeFromTiles(9, 20), self.level)
                print(self.fruit)
        if self.fruit is not None:
            if self.pacman.collideCheck(self.fruit):
                self.updateScore(self.fruit.points)
                self.textgroup.addText(str(self.fruit.points), WHITE, self.fruit.position.x, self.fruit.position.y, 8,
                                       time=1)
                fruitCaptured = False
                for fruit in self.fruitCaptured:
                    if fruit.get_offset() == self.fruit.image.get_offset():
                        fruitCaptured = True
                        break
                if not fruitCaptured:
                    self.fruitCaptured.append(self.fruit.image)
                self.fruit = None
            elif self.fruit.destroy:
                self.fruit = None

    def showEntities(self):
        self.pacman.visible = True
        self.ghosts.show()

    def hideEntities(self):
        self.pacman.visible = False
        self.ghosts.hide()

    def nextLevel(self):
        self.showEntities()
        self.level += 1
        self.pause.paused = True
        self.startGame()
        self.textgroup.updateLevel(self.level)

    def restartGame(self):
        self.lives = 5
        self.level = 0
        self.pause.paused = True
        self.fruit = None
        self.startGame()
        self.score = 0
        self.textgroup.updateScore(self.score)
        self.textgroup.updateLevel(self.level)
        self.textgroup.showText(READYTXT)
        self.lifesprites.resetLives(self.lives)
        self.fruitCaptured = []

    def resetLevel(self):
        self.pause.paused = True
        self.pacman.reset()
        self.ghosts.reset()
        self.fruit = None
        self.textgroup.showText(READYTXT)

    def updateScore(self, points):
        self.score += points
        self.textgroup.updateScore(self.score)

    def render(self):
        self.screen.blit(self.background, (0, 0))
        # self.nodes.render(self.screen)
        self.pellets.render(self.screen)
        if self.fruit is not None:
            self.fruit.render(self.screen)
        self.pacman.render(self.screen)
        self.ghosts.render(self.screen)
        self.textgroup.render(self.screen)

        for i in range(len(self.lifesprites.images)):
            x = self.lifesprites.images[i].get_width() * i
            y = SCREENHEIGHT - self.lifesprites.images[i].get_height()
            self.screen.blit(self.lifesprites.images[i], (x, y))

        for i in range(len(self.fruitCaptured)):
            x = SCREENWIDTH - self.fruitCaptured[i].get_width() * (i + 1)
            y = SCREENHEIGHT - self.fruitCaptured[i].get_height()
            self.screen.blit(self.fruitCaptured[i], (x, y))

        pygame.display.update()


if __name__ == "__main__":
    game = GameController()
    game.startGame()
    while True:
        game.update()
