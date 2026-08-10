import math
import random
import time
from PIL import Image, ImageDraw, ImageFilter, ImageOps

# Blocks
AIR = 0
DIRT = 1
GRASS = 2
STONE = 3
WOOD = 4
LEAVES = 5
COAL = 6
DIAMOND = 7
TORCH = 8
PLANKS = 9

BLOCK_SIZE = 16
WORLD_W = 120
WORLD_H = 80

class AdvancedMCEngine:
    def __init__(self, size=(480, 480), fps=30):
        self.size = size
        self.width, self.height = size
        self.fps = fps
        self.running = False
        
        self.textures = self.generate_textures()
        self.world = [[AIR for _ in range(WORLD_H)] for _ in range(WORLD_W)]
        self.torches = set() # (bx, by)
        
        self.generate_world()
        
        self.world_img = Image.new('RGB', (WORLD_W * BLOCK_SIZE, WORLD_H * BLOCK_SIZE), (135, 206, 235))
        self.render_full_world()
        
        # Day/Night Cycle
        self.time_of_day = 0 # 0 to 2400 (like Minecraft, 0=dawn, 600=noon, 1200=dusk, 1800=midnight)
        self.day_speed = 2 # Advance per frame
        
        # Player
        self.px = (WORLD_W // 2) * BLOCK_SIZE
        self.py = 0
        for y in range(WORLD_H):
            if self.world[WORLD_W // 2][y] != AIR:
                self.py = (y - 2) * BLOCK_SIZE
                break
                
        self.vx = 0.0
        self.vy = 0.0
        self.facing = 1
        self.state = 'WALK'
        self.state_timer = 0
        self.target_bx = -1
        self.target_by = -1
        
        self.inventory = {DIRT: 0, STONE: 0, WOOD: 0, PLANKS: 10, TORCH: 10}
        
        # Precompute light mask for torches
        self.torch_light = Image.new('L', (BLOCK_SIZE*8, BLOCK_SIZE*8), 0)
        draw = ImageDraw.Draw(self.torch_light)
        for r in range(BLOCK_SIZE*4, 0, -2):
            alpha = int(255 * (1 - r/(BLOCK_SIZE*4)))
            draw.ellipse([BLOCK_SIZE*4 - r, BLOCK_SIZE*4 - r, BLOCK_SIZE*4 + r, BLOCK_SIZE*4 + r], fill=alpha)
            
    def generate_textures(self):
        tex = {}
        def make_tex(base, noise, amt=0.2):
            img = Image.new('RGB', (BLOCK_SIZE, BLOCK_SIZE), base)
            pixels = img.load()
            for x in range(BLOCK_SIZE):
                for y in range(BLOCK_SIZE):
                    if random.random() < amt:
                        pixels[x, y] = noise
            return img

        tex[DIRT] = make_tex((101, 67, 33), (80, 50, 20))
        grass = tex[DIRT].copy()
        draw = ImageDraw.Draw(grass)
        draw.rectangle([0, 0, BLOCK_SIZE, 4], fill=(34, 139, 34))
        for i in range(BLOCK_SIZE):
            if random.random() < 0.5:
                draw.point((i, 5), fill=(34, 139, 34))
        tex[GRASS] = grass
        tex[STONE] = make_tex((128, 128, 128), (100, 100, 100))
        tex[WOOD] = make_tex((92, 64, 51), (70, 45, 30), 0.5)
        tex[LEAVES] = make_tex((34, 139, 34), (0, 100, 0), 0.4)
        tex[PLANKS] = make_tex((205, 133, 63), (160, 82, 45), 0.1)
        draw = ImageDraw.Draw(tex[PLANKS])
        draw.line([0, 4, BLOCK_SIZE, 4], fill=(139, 69, 19))
        draw.line([0, 10, BLOCK_SIZE, 10], fill=(139, 69, 19))
        
        coal = tex[STONE].copy()
        draw = ImageDraw.Draw(coal)
        for _ in range(8): draw.point((random.randint(2,13), random.randint(2,13)), fill=(20,20,20))
        tex[COAL] = coal
        
        dia = tex[STONE].copy()
        draw = ImageDraw.Draw(dia)
        for _ in range(6): draw.point((random.randint(2,13), random.randint(2,13)), fill=(0, 255, 255))
        tex[DIAMOND] = dia
        
        torch = Image.new('RGBA', (BLOCK_SIZE, BLOCK_SIZE), (0,0,0,0))
        draw = ImageDraw.Draw(torch)
        draw.rectangle([6, 8, 9, 15], fill=(101, 67, 33))
        draw.rectangle([6, 5, 9, 8], fill=(255, 200, 0))
        draw.rectangle([7, 4, 8, 6], fill=(255, 255, 200))
        # Crear textura RGB con fondo negro para pegar si no soporta alpha directo fácil
        # Usaremos alpha composite manual o pegar con máscara
        tex[TORCH] = torch
        
        return tex

    def generate_world(self):
        h = 25
        for x in range(WORLD_W):
            if random.random() < 0.3:
                h += random.choice([-1, 1, 0])
            h = max(15, min(35, h))
            
            for y in range(WORLD_H):
                if y < h:
                    self.world[x][y] = AIR
                elif y == h:
                    self.world[x][y] = GRASS
                elif y < h + 5:
                    self.world[x][y] = DIRT
                else:
                    self.world[x][y] = STONE
                    if random.random() < 0.05:
                        self.world[x][y] = COAL
                    elif y > 60 and random.random() < 0.02:
                        self.world[x][y] = DIAMOND

        # Caves (random worms)
        for _ in range(20):
            cx, cy = random.randint(5, WORLD_W-5), random.randint(40, WORLD_H-5)
            for _ in range(random.randint(20, 50)):
                if 0 <= cx < WORLD_W and 0 <= cy < WORLD_H:
                    self.world[cx][cy] = AIR
                    for dx, dy in [(1,0), (-1,0), (0,1), (0,-1), (1,1), (-1,-1)]:
                        if 0 <= cx+dx < WORLD_W and 0 <= cy+dy < WORLD_H and random.random()<0.5:
                            self.world[cx+dx][cy+dy] = AIR
                cx += random.choice([-1, 1, 0])
                cy += random.choice([-1, 1, 0])

        # Trees
        for x in range(5, WORLD_W - 5, 8):
            if random.random() < 0.5:
                for y in range(WORLD_H):
                    if self.world[x][y] == GRASS:
                        # Tronco
                        for th in range(1, 5):
                            self.world[x][y - th] = WOOD
                        # Hojas
                        for lx in range(x - 2, x + 3):
                            for ly in range(y - 7, y - 4):
                                self.world[lx][ly] = LEAVES
                        self.world[x][y - 8] = LEAVES
                        self.world[x-1][y-8] = LEAVES
                        self.world[x+1][y-8] = LEAVES
                        break

    def render_full_world(self):
        self.world_img.paste((135, 206, 235), [0, 0, self.world_img.width, self.world_img.height])
        for x in range(WORLD_W):
            for y in range(WORLD_H):
                b = self.world[x][y]
                if b != AIR:
                    if b == TORCH:
                        self.world_img.paste(self.textures[b], (x * BLOCK_SIZE, y * BLOCK_SIZE), self.textures[b])
                    else:
                        self.world_img.paste(self.textures[b], (x * BLOCK_SIZE, y * BLOCK_SIZE))

    def update_block(self, bx, by, block_id):
        if 0 <= bx < WORLD_W and 0 <= by < WORLD_H:
            old_block = self.world[bx][by]
            if old_block == TORCH and (bx, by) in self.torches:
                self.torches.remove((bx, by))
            
            self.world[bx][by] = block_id
            px = bx * BLOCK_SIZE
            py = by * BLOCK_SIZE
            
            if block_id == AIR:
                self.world_img.paste((135, 206, 235), [px, py, px + BLOCK_SIZE, py + BLOCK_SIZE])
            elif block_id == TORCH:
                self.torches.add((bx, by))
                self.world_img.paste(self.textures[block_id], (px, py), self.textures[block_id])
            else:
                self.world_img.paste(self.textures[block_id], (px, py))

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def is_solid(self, bx, by):
        if bx < 0 or bx >= WORLD_W or by < 0 or by >= WORLD_H:
            return True
        return self.world[bx][by] not in [AIR, LEAVES, TORCH]

    def update(self):
        # Avanzar tiempo
        self.time_of_day = (self.time_of_day + self.day_speed) % 2400
        
        # Físicas
        self.vy += 1.0 # Gravedad
        if self.vy > 10: self.vy = 10
        
        next_y = self.py + self.vy
        foot_bx = int((self.px + BLOCK_SIZE/2) // BLOCK_SIZE)
        foot_by = int((next_y + BLOCK_SIZE*1.5) // BLOCK_SIZE)
        
        on_ground = False
        if self.vy > 0 and self.is_solid(foot_bx, foot_by):
            self.py = foot_by * BLOCK_SIZE - BLOCK_SIZE*1.5
            self.vy = 0
            on_ground = True
        else:
            self.py = next_y
            
        next_x = self.px + self.vx
        side_bx = int((next_x + (BLOCK_SIZE if self.vx > 0 else 0)) // BLOCK_SIZE)
        mid_y1 = int(self.py // BLOCK_SIZE)
        mid_y2 = int((self.py + BLOCK_SIZE) // BLOCK_SIZE)
        
        blocked = False
        if self.is_solid(side_bx, mid_y1) or self.is_solid(side_bx, mid_y2):
            self.px = side_bx * BLOCK_SIZE - (BLOCK_SIZE if self.vx > 0 else -BLOCK_SIZE)
            self.vx = 0
            blocked = True
        else:
            self.px = next_x
            
        if self.px < 0: self.px = 0
        if self.px > WORLD_W * BLOCK_SIZE - BLOCK_SIZE: self.px = WORLD_W * BLOCK_SIZE - BLOCK_SIZE

        # IA Avanzada
        self.state_timer -= 1
        
        is_night = 1200 < self.time_of_day < 2200
        
        bx = int(self.px // BLOCK_SIZE)
        by = int(self.py // BLOCK_SIZE)
        
        if self.state == 'THINK':
            if self.state_timer <= 0:
                if is_night and by < 40:
                    self.state = 'HIDE'
                else:
                    self.state = 'WALK'
                    self.facing = random.choice([-1, 1])
                    self.vx = 2 * self.facing
                    self.state_timer = random.randint(30, 100)
                    
        elif self.state == 'WALK':
            if is_night and by < 40:
                self.state = 'THINK'
                self.state_timer = 0
                self.vx = 0
                
            # Peligro de caída / hueco
            hole_bx = bx + self.facing
            hole_by = by + 2
            if not self.is_solid(hole_bx, hole_by) and not self.is_solid(hole_bx, hole_by + 1):
                # Puente
                if self.inventory[DIRT] > 0 or self.inventory[STONE] > 0 or self.inventory[PLANKS] > 0:
                    self.state = 'BRIDGE'
                    self.target_bx = hole_bx
                    self.target_by = hole_by
                    self.state_timer = 15
                    self.vx = 0
                else:
                    self.facing *= -1
                    self.vx = 2 * self.facing

            if blocked and on_ground:
                wall_bx = bx + self.facing
                wall_by = by + 1
                wall_by_head = by
                
                # Intentar saltar si hay 1 bloque
                if self.is_solid(wall_bx, wall_by) and not self.is_solid(wall_bx, wall_by_head):
                    self.vy = -7.0
                elif self.is_solid(wall_bx, wall_by_head):
                    # Minar pared
                    self.state = 'MINE'
                    self.target_bx = wall_bx
                    self.target_by = wall_by_head if random.random()<0.5 else wall_by
                    self.state_timer = 20
                    self.vx = 0
                    
            if self.state_timer <= 0:
                self.state = 'THINK'
                self.vx = 0
                
        elif self.state == 'MINE':
            if self.state_timer <= 0:
                if 0 <= self.target_bx < WORLD_W and 0 <= self.target_by < WORLD_H:
                    b = self.world[self.target_bx][self.target_by]
                    if b in self.inventory: self.inventory[b] += 1
                    self.update_block(self.target_bx, self.target_by, AIR)
                self.target_bx = -1
                self.state = 'THINK'
                
        elif self.state == 'BRIDGE':
            if self.state_timer <= 0:
                if 0 <= self.target_bx < WORLD_W and 0 <= self.target_by < WORLD_H:
                    if self.inventory[DIRT] > 0:
                        self.update_block(self.target_bx, self.target_by, DIRT)
                        self.inventory[DIRT] -= 1
                    elif self.inventory[STONE] > 0:
                        self.update_block(self.target_bx, self.target_by, STONE)
                        self.inventory[STONE] -= 1
                    elif self.inventory[PLANKS] > 0:
                        self.update_block(self.target_bx, self.target_by, PLANKS)
                        self.inventory[PLANKS] -= 1
                self.state = 'WALK'
                self.state_timer = 30
                self.vx = 2 * self.facing
                
        elif self.state == 'HIDE':
            # Excavar un agujero de 3x1 y taparse, y poner antorcha
            self.vx = 0
            if on_ground:
                if not self.is_solid(bx, by + 2):
                    self.vy = 2
                else:
                    # Minar bloque de abajo
                    self.update_block(bx, by + 2, AIR)
                    # Tapar arriba
                    if self.inventory[DIRT] > 0:
                        self.update_block(bx, by - 1, DIRT)
                    elif self.inventory[PLANKS] > 0:
                        self.update_block(bx, by - 1, PLANKS)
                    
                    # Antorcha
                    if self.inventory[TORCH] > 0 and self.world[bx][by] == AIR:
                        self.update_block(bx, by, TORCH)
                        self.inventory[TORCH] -= 1
                    
                    # Esperar hasta de día
                    if not is_night:
                        self.state = 'MINE'
                        self.target_bx = bx
                        self.target_by = by - 1
                        self.state_timer = 20

    def get_frame(self):
        self.update()
        
        cam_x = int(self.px) - self.width // 2
        cam_y = int(self.py) - self.height // 2
        cam_x = max(0, min(cam_x, WORLD_W * BLOCK_SIZE - self.width))
        cam_y = max(0, min(cam_y, WORLD_H * BLOCK_SIZE - self.height))
        
        frame = self.world_img.crop((cam_x, cam_y, cam_x + self.width, cam_y + self.height)).convert("RGBA")
        
        # Color del cielo por el ciclo de día
        sky_color = (135, 206, 235)
        darkness_alpha = 0
        if 1000 < self.time_of_day < 1400: # Atardecer
            progress = (self.time_of_day - 1000) / 400.0
            sky_color = (int(135 + progress*100), int(206 - progress*100), int(235 - progress*100))
            darkness_alpha = int(progress * 220)
        elif 1400 <= self.time_of_day <= 2000: # Noche
            sky_color = (20, 20, 40)
            darkness_alpha = 220
        elif 2000 < self.time_of_day < 2400: # Amanecer
            progress = (self.time_of_day - 2000) / 400.0
            sky_color = (int(20 + progress*115), int(20 + progress*186), int(40 + progress*195))
            darkness_alpha = int((1.0 - progress) * 220)
            
        # Re-teñir el cielo si es visible (muy básico: llenar todo con sky y mezclar)
        # Una forma más barata es tener un overlay de oscuridad general
        
        # Dibujar Jugador
        draw = ImageDraw.Draw(frame)
        rel_x = int(self.px) - cam_x
        rel_y = int(self.py) - cam_y
        
        # Jugador
        draw.rectangle([rel_x + 2, rel_y + 8, rel_x + 14, rel_y + 16], fill=(0, 200, 200)) # Camisa
        draw.rectangle([rel_x + 2, rel_y + 16, rel_x + 14, rel_y + 24], fill=(0, 0, 200)) # Pantalones
        draw.rectangle([rel_x + 4, rel_y, rel_x + 12, rel_y + 8], fill=(255, 200, 150)) # Cabeza
        eye_x = rel_x + 8 if self.facing == 1 else rel_x + 5
        draw.rectangle([eye_x, rel_y + 2, eye_x + 1, rel_y + 3], fill=(0, 0, 0)) # Ojo
        
        if self.state == 'MINE' and self.target_bx != -1:
            tx = self.target_bx * BLOCK_SIZE - cam_x
            ty = self.target_by * BLOCK_SIZE - cam_y
            draw.line([rel_x + 8, rel_y + 12, tx + 8, ty + 8], fill=(150, 150, 150), width=2)
            if self.state_timer < 10:
                draw.line([tx+4, ty+4, tx+12, ty+12], fill=(0,0,0), width=1)
                
        # Iluminación
        # Overlay oscuro
        if darkness_alpha > 0 or cam_y > 40 * BLOCK_SIZE:
            # En cuevas (cam_y alto) siempre es oscuro
            cave_darkness = max(0, min(230, (cam_y - 30 * BLOCK_SIZE) / 2))
            final_dark = max(darkness_alpha, cave_darkness)
            
            dark_overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, int(final_dark)))
            
            # Recortar antorchas
            mask = Image.new('L', (self.width, self.height), int(final_dark))
            mask_draw = ImageDraw.Draw(mask)
            
            for (bx, by) in self.torches:
                tx = bx * BLOCK_SIZE - cam_x + BLOCK_SIZE//2
                ty = by * BLOCK_SIZE - cam_y + BLOCK_SIZE//2
                if -64 < tx < self.width + 64 and -64 < ty < self.height + 64:
                    # Pegar luz radial restando opacidad
                    mask.paste(self.torch_light, (tx - 64, ty - 64), self.torch_light)
                    
            # Invertir máscara y aplicar al overlay
            dark_overlay.putalpha(ImageOps.invert(mask))
            frame.alpha_composite(dark_overlay)
            
        return frame.convert("RGB")
