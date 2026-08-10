import math
import random
import time
from PIL import Image, ImageDraw, ImageFont, ImageOps

AIR = 0
DIRT = 1
GRASS = 2
STONE = 3
WOOD = 4
LEAVES = 5
COAL = 6
DIAMOND = 7
TORCH = 8

BLOCK_SIZE = 16
SCREEN_W = 480
SCREEN_H = 480
BLOCKS_W = SCREEN_W // BLOCK_SIZE
BLOCKS_H = SCREEN_H // BLOCK_SIZE

class UltraMCEngine:
    def __init__(self, fps=30):
        self.fps = fps
        self.running = False
        
        self.textures = self.generate_textures()
        self.world = {} # (bx, by) -> block_id
        self.torches = set()
        self.generated_columns = set()
        
        # Day/Night Cycle
        self.time_of_day = 0 # 0 to 2400
        self.day_speed = 2
        
        # Player
        self.px = 0.0
        self.py = 0.0
        
        # Generar columna inicial para situar al jugador
        self.generate_column(0)
        for y in range(100):
            if self.world.get((0, y), AIR) != AIR:
                self.py = (y - 2) * BLOCK_SIZE
                break
                
        self.vx = 0.0
        self.vy = 0.0
        self.facing = 1
        
        self.state = 'THINK'
        self.state_timer = 0
        self.target_bx = -1
        self.target_by = -1
        
        self.inventory = {DIRT: 10, STONE: 0, WOOD: 0, COAL: 0, DIAMOND: 0, TORCH: 20}
        
        # Precompute darkness overlays
        self.dark_overlays = []
        for i in range(16):
            alpha = 255 - (i * 17)
            img = Image.new('RGBA', (BLOCK_SIZE, BLOCK_SIZE), (0, 0, 0, alpha))
            self.dark_overlays.append(img)
            
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
        tex[TORCH] = torch
        return tex

    def generate_column(self, bx):
        if bx in self.generated_columns: return
        h = 30 + int(math.sin(bx * 0.1) * 5 + math.sin(bx * 0.03) * 10 + math.sin(bx * 0.5) * 2)
        
        for by in range(h, h+5):
            self.world[(bx, by)] = DIRT
        self.world[(bx, h)] = GRASS
        for by in range(h+5, 100):
            self.world[(bx, by)] = STONE
            if random.random() < 0.04: self.world[(bx, by)] = COAL
            if by > 60 and random.random() < 0.01: self.world[(bx, by)] = DIAMOND
            
        # Cueva gusano simplificada
        if bx % 10 == 0:
            cx, cy = bx, random.randint(40, 80)
            for _ in range(30):
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        self.world[(cx+dx, cy+dy)] = AIR
                cx += random.choice([-1, 1])
                cy += random.choice([-1, 1, 0])
                
        # Árboles
        if random.random() < 0.08:
            for th in range(1, 5): self.world[(bx, h - th)] = WOOD
            for lx in range(bx - 2, bx + 3):
                for ly in range(h - 7, h - 4): self.world[(lx, ly)] = LEAVES
            self.world[(bx, h - 8)] = LEAVES
            
        self.generated_columns.add(bx)

    def is_solid(self, bx, by):
        b = self.world.get((bx, by), AIR)
        return b not in [AIR, LEAVES, TORCH]
        
    def set_block(self, bx, by, b_id):
        self.world[(bx, by)] = b_id
        if b_id == TORCH:
            self.torches.add((bx, by))
        else:
            if (bx, by) in self.torches:
                self.torches.remove((bx, by))

    def update(self):
        self.time_of_day = (self.time_of_day + self.day_speed) % 2400
        
        cam_bx = int(self.px // BLOCK_SIZE)
        for bx in range(cam_bx - 20, cam_bx + 20):
            if bx not in self.generated_columns:
                self.generate_column(bx)
                
        # Física
        self.vy += 1.0
        if self.vy > 10: self.vy = 10
        
        next_y = self.py + self.vy
        foot_bx = int((self.px + 8) // BLOCK_SIZE)
        foot_by = int((next_y + 24) // BLOCK_SIZE)
        
        on_ground = False
        if self.vy > 0 and self.is_solid(foot_bx, foot_by):
            self.py = foot_by * BLOCK_SIZE - 24
            self.vy = 0
            on_ground = True
        else:
            self.py = next_y
            
        next_x = self.px + self.vx
        side_bx = int((next_x + (16 if self.vx > 0 else 0)) // BLOCK_SIZE)
        mid_y1 = int((self.py + 4) // BLOCK_SIZE)
        mid_y2 = int((self.py + 20) // BLOCK_SIZE)
        
        blocked = False
        if self.is_solid(side_bx, mid_y1) or self.is_solid(side_bx, mid_y2):
            self.px = side_bx * BLOCK_SIZE - (16 if self.vx > 0 else -BLOCK_SIZE)
            self.vx = 0
            blocked = True
        else:
            self.px = next_x

        # IA Ultra
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
                    self.vx = 2.5 * self.facing
                    self.state_timer = random.randint(30, 90)
                    
        elif self.state == 'WALK':
            if is_night and by < 40:
                self.state = 'THINK'
                self.state_timer = 0
                self.vx = 0
                
            hole_bx = bx + self.facing
            hole_by = by + 2
            if not self.is_solid(hole_bx, hole_by) and not self.is_solid(hole_bx, hole_by + 1):
                if self.inventory[DIRT] > 0:
                    self.state = 'BRIDGE'
                    self.target_bx = hole_bx
                    self.target_by = hole_by
                    self.state_timer = 15
                    self.vx = 0
                else:
                    self.facing *= -1
                    self.vx = 2.5 * self.facing

            if blocked and on_ground:
                wall_bx = bx + self.facing
                wall_by = by + 1
                wall_by_head = by
                if self.is_solid(wall_bx, wall_by) and not self.is_solid(wall_bx, wall_by_head):
                    self.vy = -7.0
                elif self.is_solid(wall_bx, wall_by_head):
                    self.state = 'MINE'
                    self.target_bx = wall_bx
                    self.target_by = wall_by_head if random.random()<0.5 else wall_by
                    self.state_timer = 15
                    self.vx = 0
                    
            if self.state_timer <= 0:
                self.state = 'THINK'
                self.vx = 0
                
        elif self.state == 'MINE':
            if self.state_timer <= 0:
                b = self.world.get((self.target_bx, self.target_by), AIR)
                if b in self.inventory: self.inventory[b] += 1
                self.set_block(self.target_bx, self.target_by, AIR)
                self.target_bx = -1
                self.state = 'THINK'
                
        elif self.state == 'BRIDGE':
            if self.state_timer <= 0:
                if self.inventory[DIRT] > 0:
                    self.set_block(self.target_bx, self.target_by, DIRT)
                    self.inventory[DIRT] -= 1
                self.state = 'WALK'
                self.state_timer = 30
                self.vx = 2.5 * self.facing
                
        elif self.state == 'HIDE':
            self.vx = 0
            if on_ground:
                if not self.is_solid(bx, by + 2):
                    self.vy = 2
                else:
                    self.set_block(bx, by + 2, AIR)
                    if self.inventory[DIRT] > 0:
                        self.set_block(bx, by - 1, DIRT)
                    if self.inventory[TORCH] > 0 and self.world.get((bx, by), AIR) == AIR:
                        self.set_block(bx, by, TORCH)
                        self.inventory[TORCH] -= 1
                    if not is_night:
                        self.state = 'MINE'
                        self.target_bx = bx
                        self.target_by = by - 1
                        self.state_timer = 20

    def get_frame(self):
        self.update()
        cam_x = int(self.px) - SCREEN_W // 2
        cam_y = int(self.py) - SCREEN_H // 2
        cam_x = max(-1000000, min(cam_x, 1000000))
        cam_y = max(-1000, min(cam_y, 100 * BLOCK_SIZE))
        
        frame = Image.new('RGB', (SCREEN_W, SCREEN_H), (135, 206, 235))
        
        # Sky color
        if 1000 < self.time_of_day < 1400:
            p = (self.time_of_day - 1000) / 400.0
            frame.paste((int(135 - p*115), int(206 - p*186), int(235 - p*195)), [0,0,SCREEN_W,SCREEN_H])
        elif 1400 <= self.time_of_day <= 2000:
            frame.paste((20, 20, 40), [0,0,SCREEN_W,SCREEN_H])
        elif 2000 < self.time_of_day < 2400:
            p = (self.time_of_day - 2000) / 400.0
            frame.paste((int(20 + p*115), int(20 + p*186), int(40 + p*195)), [0,0,SCREEN_W,SCREEN_H])

        cam_bx = cam_x // BLOCK_SIZE
        cam_by = cam_y // BLOCK_SIZE
        
        # Calcular Luz
        light_map = {}
        for bx in range(cam_bx - 1, cam_bx + BLOCKS_W + 2):
            sky_light = 15 if not (1000 < self.time_of_day < 2400) else 4
            for by in range(0, cam_by + BLOCKS_H + 2):
                if self.is_solid(bx, by): sky_light = 0
                light_map[(bx, by)] = sky_light
                
        for (tx, ty) in self.torches:
            if cam_bx - 2 < tx < cam_bx + BLOCKS_W + 2 and cam_by - 2 < ty < cam_by + BLOCKS_H + 2:
                light_map[(tx, ty)] = 15
                
        # Propagar luz rápido (2 iteraciones)
        for _ in range(2):
            new_light = light_map.copy()
            for bx in range(cam_bx, cam_bx + BLOCKS_W + 1):
                for by in range(max(0, cam_by), cam_by + BLOCKS_H + 1):
                    mx = light_map.get((bx, by), 0)
                    if mx < 15:
                        n = max(light_map.get((bx+1, by), 0), light_map.get((bx-1, by), 0),
                                light_map.get((bx, by+1), 0), light_map.get((bx, by-1), 0))
                        if n > mx + 2: new_light[(bx, by)] = n - 2
            light_map = new_light

        # Dibujar Bloques e Iluminación
        for bx in range(cam_bx, cam_bx + BLOCKS_W + 1):
            for by in range(cam_by, cam_by + BLOCKS_H + 1):
                b = self.world.get((bx, by), AIR)
                sx = bx * BLOCK_SIZE - cam_x
                sy = by * BLOCK_SIZE - cam_y
                if b != AIR:
                    if b == TORCH:
                        frame.paste(self.textures[b], (sx, sy), self.textures[b])
                    else:
                        frame.paste(self.textures[b], (sx, sy))
                
                # Sombra
                l = light_map.get((bx, by), 0)
                if l < 15:
                    frame.paste(self.dark_overlays[l], (sx, sy), self.dark_overlays[l])

        # Jugador
        draw = ImageDraw.Draw(frame)
        rx = int(self.px) - cam_x
        ry = int(self.py) - cam_y
        draw.rectangle([rx+4, ry+8, rx+12, ry+16], fill=(0, 200, 200))
        draw.rectangle([rx+4, ry+16, rx+12, ry+24], fill=(0, 0, 200))
        draw.rectangle([rx+4, ry, rx+12, ry+8], fill=(255, 200, 150))
        ex = rx+9 if self.facing == 1 else rx+6
        draw.rectangle([ex, ry+2, ex+1, ry+3], fill=(0,0,0))
        
        # Pico
        if self.state == 'MINE':
            draw.line([rx+8, ry+12, rx+8+10*self.facing, ry+12], fill=(139,69,19), width=2)
            draw.line([rx+8+10*self.facing, ry+8, rx+8+10*self.facing, ry+16], fill=(150,150,150), width=3)
            
        # UI HUD (Inventario)
        hud_y = SCREEN_H - 40
        draw.rectangle([0, hud_y, SCREEN_W, SCREEN_H], fill=(50, 50, 50, 200))
        items = [(WOOD, "Madera"), (DIRT, "Tierra"), (STONE, "Piedra"), (COAL, "Carbon"), (DIAMOND, "Diamante"), (TORCH, "Antorchas")]
        for i, (b_id, name) in enumerate(items):
            x = 10 + i * 70
            frame.paste(self.textures[b_id] if b_id != TORCH else self.textures[DIRT], (x, hud_y + 10)) # Placeholder
            if b_id == TORCH: frame.paste(self.textures[TORCH], (x, hud_y + 10), self.textures[TORCH])
            qty = self.inventory.get(b_id, 0)
            draw.text((x + 20, hud_y + 12), f"x{qty}", fill=(255,255,255))

        return frame

    def start(self): self.running = True
    def stop(self): self.running = False
