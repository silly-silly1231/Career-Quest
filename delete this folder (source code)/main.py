# main.py

import sys


sys.dont_write_bytecode = True

import pygame
from source.game.game_manager import GameManager

def main():
    pygame.init()
    game = GameManager()
    game.run()
    pygame.quit()

if __name__ == "__main__":
    main()