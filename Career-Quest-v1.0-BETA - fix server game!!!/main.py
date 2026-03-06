# main.py

import sys

# Prevent Python from generating __pycache__ and .pyc files.
sys.dont_write_bytecode = True

import pygame
from game.game_manager import GameManager

def main():
    pygame.init()
    game = GameManager()
    game.run()
    pygame.quit()

if __name__ == "__main__":
    main()  