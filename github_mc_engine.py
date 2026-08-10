import os
import time
import math
import random
from PIL import Image

# Forzar Pygame a modo Headless (sin ventana)
os.environ['SDL_VIDEODRIVER'] = 'dummy'
import pygame

from data.scripts.classes.player import Player
from data.scripts.classes.terrain import Terrain
from data.scripts.classes.hotbar import Hotbar
from data.scripts.core_functions import draw, distance
import data.variables as variables

class GithubMCEngine:
    def __init__(self, fps=30):
        self.fps = fps
        self.running = False
        
        pygame.init()
        self.screen = pygame.display.set_mode(variables.WINDOW_SIZE)
        
        # Iniciar entidades del juego de GitHub
        self.player = Player((0, -200), variables.TILE_SIZE-10, variables.TILE_SIZE*2-10, 5, 12)
        self.hotbar = Hotbar()
        self.terrain = Terrain()
        self.terrain.generate_chunk(0, 0)
        
        # Variables de la IA
        self.ai_state = 'IDLE'
        self.ai_timer = 0
        self.ai_target_coords = None

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def ai_tick(self):
        # Esta es la IA que "hackea" los controles del jugador
        self.player.moving_left = False
        self.player.moving_right = False
        
        # Objetivo 1: Recolectar bloques y construir
        # El jugador de Github tiene self.inventory y self.coords
        
        if self.ai_state == 'IDLE':
            self.ai_timer -= 1
            if self.ai_timer <= 0:
                self.ai_state = 'EXPLORE'
                self.ai_timer = random.randint(30, 100)
                self.ai_dir = random.choice([-1, 1])
                
        elif self.ai_state == 'EXPLORE':
            self.ai_timer -= 1
            if self.ai_dir == 1:
                self.player.moving_right = True
            else:
                self.player.moving_left = True
                
            # Detectar obstáculo enfrente para minarlo o saltar
            # En el juego de GitHub, el player tiene pixel_coords
            px, py = self.player.pixel_coords
            ts = variables.TILE_SIZE
            
            # Revisar terreno de forma básica (el mapa de Terrain.map)
            front_x = self.player.coords[0] + self.ai_dir
            front_y = self.player.coords[1]
            
            blocked = False
            target_block = None
            for block in self.terrain.map:
                if block.coords == (front_x, front_y):
                    blocked = True
                    target_block = block
                    break
                    
            if blocked:
                # Intentar saltar
                self.player.jumping = True
                
                # O minar virtualmente
                if self.ai_timer % 15 == 0 and target_block:
                    # Simular selección de ratón (esto es un hack del código original)
                    variables.scroll[0] = self.player.rect.x - variables.WINDOW_SIZE[0]//2
                    variables.scroll[1] = self.player.rect.y - variables.WINDOW_SIZE[1]//2
                    mx = target_block.x - variables.scroll[0] + 5
                    my = target_block.y - variables.scroll[1] + 5
                    self.player.get_selected_block(self.terrain, mx, my)
                    if self.player.selected_block:
                        self.player.break_block(self.terrain, self.hotbar)
            
            if self.ai_timer <= 0:
                self.ai_state = 'IDLE'
                self.ai_timer = 20
                
        # Simular física de salto (porque hemos quitado el evento KEYUP)
        # El jugador internamente gestiona su salto, pero la IA lo pulsa.
        
    def update(self):
        # Lógica de cámara (scroll) del código original
        variables.scroll[0] += int(
            (self.player.rect.x - variables.scroll[0] - (variables.WINDOW_SIZE[0]/2 + self.player.width/2 - 50)) / variables.SCROLL_STIFF
        )
        variables.scroll[1] += int(
            (self.player.rect.y - variables.scroll[1] - (variables.WINDOW_SIZE[1]/2 + self.player.height/2 - 100)) / variables.SCROLL_STIFF
        )
        
        # Actualizar IA
        self.ai_tick()
        
        # Limpiar Chunks como el original
        for chunk in list(set([i.chunk for i in self.terrain.map])):
            if distance(self.player.current_chunk, chunk) >= variables.RENDER_DISTANCE:
                self.terrain.unload_chunk(chunk)
                
        # Mantener el bloque seleccionado aunque no haya ratón real (si la IA no lo cambia)
        
        self.terrain.update(self.player)
        self.player.update(self.terrain)
        self.hotbar.update()
        
        draw(self.screen, self.terrain, self.player, self.hotbar)

    def get_frame(self):
        self.update()
        # Capturar la superficie de Pygame
        # tostring está obsoleto pero funciona, tobytes es mejor
        try:
            raw_data = pygame.image.tobytes(self.screen, 'RGB')
        except AttributeError:
            raw_data = pygame.image.tostring(self.screen, 'RGB')
            
        img = Image.frombytes('RGB', variables.WINDOW_SIZE, raw_data)
        return img
