import math
import random
import time
from PIL import Image, ImageDraw

# IDs de Bloques
AIR = 0
DIRT = 1
GRASS = 2
STONE = 3
WOOD = 4
LEAVES = 5

BLOCK_SIZE = 24
WORLD_W = 80
WORLD_H = 20

class TerrariaEngine:
    def __init__(self, size=(480, 480), fps=30):
        self.size = size
        self.width, self.height = size
        self.fps = fps
        self.running = False
        
        # Texturas pre-generadas
        self.textures = self.generate_textures()
        
        # Generar mundo
        self.world = [[AIR for _ in range(WORLD_H)] for _ in range(WORLD_W)]
        self.generate_world()
        
        # Renderizado estático del mundo (para optimizar)
        self.world_img = Image.new('RGB', (WORLD_W * BLOCK_SIZE, WORLD_H * BLOCK_SIZE), (135, 206, 235))
        self.render_full_world()
        
        # Jugador (IA)
        self.px = (WORLD_W // 2) * BLOCK_SIZE
        self.py = 0
        # Encontrar superficie para el jugador
        for y in range(WORLD_H):
            if self.world[WORLD_W // 2][y] != AIR:
                self.py = (y - 1) * BLOCK_SIZE
                break
                
        self.vx = 0.0
        self.vy = 0.0
        self.facing = 1 # 1 derecha, -1 izquierda
        self.state = 'THINK'
        self.state_timer = 0
        
        self.target_bx = -1
        self.target_by = -1

    def generate_textures(self):
        tex = {}
        
        def make_tex(base_color, noise_color, noise_amt=0.2):
            img = Image.new('RGB', (BLOCK_SIZE, BLOCK_SIZE), base_color)
            pixels = img.load()
            for x in range(BLOCK_SIZE):
                for y in range(BLOCK_SIZE):
                    if random.random() < noise_amt:
                        pixels[x, y] = noise_color
            return img

        # Dirt
        tex[DIRT] = make_tex((101, 67, 33), (80, 50, 20))
        
        # Grass (dirt base, green top)
        grass_img = tex[DIRT].copy()
        draw = ImageDraw.Draw(grass_img)
        draw.rectangle([0, 0, BLOCK_SIZE, 5], fill=(34, 139, 34))
        for i in range(BLOCK_SIZE):
            if random.random() < 0.5:
                draw.point((i, 6), fill=(34, 139, 34))
        tex[GRASS] = grass_img
        
        # Stone
        tex[STONE] = make_tex((128, 128, 128), (100, 100, 100))
        
        # Wood
        wood = Image.new('RGB', (BLOCK_SIZE, BLOCK_SIZE), (139, 69, 19))
        draw = ImageDraw.Draw(wood)
        draw.line([6, 0, 6, BLOCK_SIZE], fill=(100, 40, 10))
        draw.line([18, 0, 18, BLOCK_SIZE], fill=(100, 40, 10))
        tex[WOOD] = wood
        
        # Leaves
        tex[LEAVES] = make_tex((0, 100, 0), (0, 80, 0), 0.4)
        
        return tex

    def generate_world(self):
        h = 12
        for x in range(WORLD_W):
            # Caminata aleatoria para colinas
            if random.random() < 0.3:
                h += random.choice([-1, 1])
            h = max(6, min(16, h))
            
            for y in range(WORLD_H):
                if y < h:
                    self.world[x][y] = AIR
                elif y == h:
                    self.world[x][y] = GRASS
                elif y < h + 3:
                    self.world[x][y] = DIRT
                else:
                    self.world[x][y] = STONE
                    
        # Añadir algunos árboles
        for i in range(5):
            tx = random.randint(5, WORLD_W - 5)
            # Encontrar suelo
            for ty in range(WORLD_H):
                if self.world[tx][ty] == GRASS:
                    # Tronco
                    for h in range(1, 4):
                        self.world[tx][ty - h] = WOOD
                    # Hojas
                    for lx in range(tx - 1, tx + 2):
                        for ly in range(ty - 5, ty - 3):
                            self.world[lx][ly] = LEAVES
                    self.world[tx][ty - 6] = LEAVES
                    break

    def render_full_world(self):
        self.world_img.paste((135, 206, 235), [0, 0, self.world_img.width, self.world_img.height])
        for x in range(WORLD_W):
            for y in range(WORLD_H):
                b = self.world[x][y]
                if b != AIR:
                    self.world_img.paste(self.textures[b], (x * BLOCK_SIZE, y * BLOCK_SIZE))

    def update_block(self, bx, by, block_id):
        if 0 <= bx < WORLD_W and 0 <= by < WORLD_H:
            self.world[bx][by] = block_id
            px = bx * BLOCK_SIZE
            py = by * BLOCK_SIZE
            if block_id == AIR:
                # Dibujar cielo
                self.world_img.paste((135, 206, 235), [px, py, px + BLOCK_SIZE, py + BLOCK_SIZE])
            else:
                self.world_img.paste(self.textures[block_id], (px, py))

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def is_solid(self, bx, by):
        if bx < 0 or bx >= WORLD_W or by < 0 or by >= WORLD_H:
            return True
        return self.world[bx][by] not in [AIR, LEAVES]

    def update(self):
        # Físicas y Gravedad
        self.vy += 1.0 # Gravedad
        if self.vy > 10: self.vy = 10
        
        # Colisión Y (Suelo)
        next_y = self.py + self.vy
        foot_bx = int((self.px + 6) // BLOCK_SIZE)
        foot_by = int((next_y + 24) // BLOCK_SIZE)
        head_by = int(next_y // BLOCK_SIZE)
        
        if self.vy > 0 and self.is_solid(foot_bx, foot_by):
            self.py = foot_by * BLOCK_SIZE - 24
            self.vy = 0
            on_ground = True
        else:
            self.py = next_y
            on_ground = False
            
        # Colisión X
        next_x = self.px + self.vx
        side_bx = int((next_x + (12 if self.vx > 0 else 0)) // BLOCK_SIZE)
        if self.is_solid(side_bx, int(self.py // BLOCK_SIZE)) or self.is_solid(side_bx, int((self.py + 23) // BLOCK_SIZE)):
            self.px = side_bx * BLOCK_SIZE - (12 if self.vx > 0 else -BLOCK_SIZE)
            self.vx = 0
            blocked = True
        else:
            self.px = next_x
            blocked = False
            
        # Limites del mundo
        if self.px < 0: self.px = 0
        if self.px > WORLD_W * BLOCK_SIZE - 12: self.px = WORLD_W * BLOCK_SIZE - 12

        # IA del Agente
        self.state_timer -= 1
        
        if self.state == 'THINK':
            if self.state_timer <= 0:
                choices = ['WALK', 'WALK', 'WALK', 'MINE', 'IDLE']
                self.state = random.choice(choices)
                if self.state == 'WALK':
                    self.facing = random.choice([-1, 1])
                    self.vx = 3 * self.facing
                    self.state_timer = random.randint(30, 90)
                elif self.state == 'MINE':
                    # Buscar bloque en frente
                    self.vx = 0
                    tx = int((self.px + 6) // BLOCK_SIZE) + self.facing
                    ty = int((self.py + 12) // BLOCK_SIZE)
                    if self.is_solid(tx, ty):
                        self.target_bx = tx
                        self.target_by = ty
                        self.state_timer = 20 # 20 frames picando
                    else:
                        self.state = 'THINK'
                        self.state_timer = 0
                elif self.state == 'IDLE':
                    self.vx = 0
                    self.state_timer = random.randint(15, 45)
                    
        elif self.state == 'WALK':
            if blocked and on_ground:
                # Intentar saltar
                self.vy = -8.0
                # Si hay una pared muy alta de 2 bloques, cambiar a minar
                wall_bx = int((self.px + 12*self.facing) // BLOCK_SIZE)
                wall_by = int((self.py - 12) // BLOCK_SIZE)
                if self.is_solid(wall_bx, wall_by):
                    self.state = 'MINE'
                    self.target_bx = wall_bx
                    self.target_by = int(self.py // BLOCK_SIZE)
                    self.state_timer = 30
                    
            if self.state_timer <= 0:
                self.state = 'THINK'
                
        elif self.state == 'MINE':
            if self.state_timer <= 0:
                # Romper el bloque!
                if 0 <= self.target_bx < WORLD_W and 0 <= self.target_by < WORLD_H:
                    self.update_block(self.target_bx, self.target_by, AIR)
                self.target_bx = -1
                self.state = 'THINK'

    def get_frame(self):
        self.update()
        
        # Cámara sigue al jugador
        cam_x = int(self.px) - self.width // 2
        cam_y = int(self.py) - self.height // 2
        
        # Limitar cámara
        cam_x = max(0, min(cam_x, WORLD_W * BLOCK_SIZE - self.width))
        cam_y = max(0, min(cam_y, WORLD_H * BLOCK_SIZE - self.height))
        
        # Cortar la vista de la imagen estática del mundo
        frame = self.world_img.crop((cam_x, cam_y, cam_x + self.width, cam_y + self.height))
        draw = ImageDraw.Draw(frame)
        
        # Dibujar Jugador (Terraria default guy)
        rel_x = int(self.px) - cam_x
        rel_y = int(self.py) - cam_y
        
        # Camiseta
        draw.rectangle([rel_x, rel_y + 8, rel_x + 12, rel_y + 18], fill=(0, 200, 0))
        # Pantalones
        draw.rectangle([rel_x, rel_y + 18, rel_x + 12, rel_y + 24], fill=(0, 0, 200))
        # Cabeza
        draw.rectangle([rel_x + 2, rel_y, rel_x + 10, rel_y + 8], fill=(255, 200, 150))
        # Ojo
        eye_x = rel_x + 7 if self.facing == 1 else rel_x + 3
        draw.rectangle([eye_x, rel_y + 2, eye_x + 2, rel_y + 4], fill=(0, 0, 0))
        
        # Dibujar pico si está minando
        if self.state == 'MINE' and self.target_bx != -1:
            tx = self.target_bx * BLOCK_SIZE - cam_x
            ty = self.target_by * BLOCK_SIZE - cam_y
            # Pico simple
            draw.line([rel_x + 6, rel_y + 12, tx + 12, ty + 12], fill=(150, 150, 150), width=2)
            # Efecto de grieta
            if self.state_timer < 10:
                draw.line([tx, ty, tx+10, ty+10], fill=(0,0,0), width=1)
                
        return frame
