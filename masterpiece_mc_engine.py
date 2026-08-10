import math
import random
import time
from PIL import Image, ImageDraw, ImageOps

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
SCREEN_W = 480
SCREEN_H = 480
BLOCKS_W = SCREEN_W // BLOCK_SIZE
BLOCKS_H = SCREEN_H // BLOCK_SIZE

class MasterpieceMCEngine:
    def __init__(self, fps=30):
        self.fps = fps
        self.running = False
        
        self.textures = self.generate_textures()
        self.world = {} # (bx, by) -> block_id
        self.torches = set()
        self.generated_columns = set()
        
        self.time_of_day = 0 # 0 to 2400
        self.day_speed = 2
        
        self.px = 0.0
        self.py = 0.0
        
        # Generar terreno inicial
        self.generate_column(0)
        for y in range(100):
            if self.world.get((0, y), AIR) != AIR:
                self.py = (y - 2) * BLOCK_SIZE
                break
                
        self.vx = 0.0
        self.vy = 0.0
        self.facing = 1
        
        # IA Orientada a Tareas (El Cerebro Perfecto)
        self.inventory = {DIRT: 0, STONE: 0, WOOD: 0, COAL: 0, DIAMOND: 0, TORCH: 20, PLANKS: 0}
        self.task_queue = [] # Lista de tuplas: ('MINE', x, y) o ('PLACE', x, y, block_id)
        self.macro_goal = 'GATHER_WOOD'
        self.action_timer = 0
        self.stuck_timer = 0
        self.last_px = 0.0
        
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
        draw.rectangle([0, 0, BLOCK_SIZE, 3], fill=(34, 139, 34))
        for i in range(BLOCK_SIZE):
            if random.random() < 0.5: draw.point((i, 4), fill=(34, 139, 34))
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
        tex[TORCH] = torch
        return tex

    def generate_column(self, bx):
        if bx in self.generated_columns: return
        h = 30 + int(math.sin(bx * 0.05) * 6 + math.sin(bx * 0.1) * 3)
        
        for by in range(h, h+5): self.world[(bx, by)] = DIRT
        self.world[(bx, h)] = GRASS
        for by in range(h+5, 100):
            self.world[(bx, by)] = STONE
            if random.random() < 0.04: self.world[(bx, by)] = COAL
            if by > 60 and random.random() < 0.01: self.world[(bx, by)] = DIAMOND
            
        if bx % 15 == 0:
            cx, cy = bx, random.randint(40, 80)
            for _ in range(25):
                for dx in range(-1, 2):
                    for dy in range(-1, 2): self.world[(cx+dx, cy+dy)] = AIR
                cx += random.choice([-1, 1])
                cy += random.choice([-1, 1, 0])
                
        if random.random() < 0.1:
            for th in range(1, 5): self.world[(bx, h - th)] = WOOD
            for lx in range(bx - 2, bx + 3):
                for ly in range(h - 7, h - 4): self.world[(lx, ly)] = LEAVES
            self.world[(bx, h - 8)] = LEAVES
            
        self.generated_columns.add(bx)

    def is_solid(self, bx, by):
        return self.world.get((bx, by), AIR) not in [AIR, LEAVES, TORCH]
        
    def set_block(self, bx, by, b_id):
        self.world[(bx, by)] = b_id
        if b_id == TORCH:
            self.torches.add((bx, by))
        else:
            if (bx, by) in self.torches:
                self.torches.remove((bx, by))

    def plan_base(self):
        bx = int(self.px // BLOCK_SIZE)
        by = int(self.py // BLOCK_SIZE)
        # Vaciar 7x5
        for x in range(bx - 3, bx + 4):
            for y in range(by - 4, by + 1):
                self.task_queue.append(('MINE', x, y))
        # Poner paredes
        for y in range(by - 4, by + 1):
            self.task_queue.append(('PLACE', bx - 3, y, PLANKS))
            self.task_queue.append(('PLACE', bx + 3, y, PLANKS))
        # Techo
        for x in range(bx - 3, bx + 4):
            self.task_queue.append(('PLACE', x, by - 4, PLANKS))
        # Antorcha
        self.task_queue.append(('PLACE', bx, by - 2, TORCH))

    def update(self):
        self.time_of_day = (self.time_of_day + self.day_speed) % 2400
        cam_bx = int(self.px // BLOCK_SIZE)
        for bx in range(cam_bx - 20, cam_bx + 20): self.generate_column(bx)
                
        # Física estricta (Punto a Punto) AABB
        self.vy += 1.0
        if self.vy > 10: self.vy = 10
        
        # Movimiento Y
        next_py = self.py + self.vy
        player_rect = [self.px + 2, next_py, self.px + 14, next_py + 24]
        
        on_ground = False
        # Chequear colisión Y
        for y in range(int(player_rect[1]//BLOCK_SIZE), int(player_rect[3]//BLOCK_SIZE) + 1):
            for x in range(int(player_rect[0]//BLOCK_SIZE), int(player_rect[2]//BLOCK_SIZE) + 1):
                if self.is_solid(x, y):
                    if self.vy > 0: # Cayendo
                        self.py = y * BLOCK_SIZE - 24.1
                        self.vy = 0
                        on_ground = True
                    elif self.vy < 0: # Saltando y choca techo
                        self.py = (y + 1) * BLOCK_SIZE + 0.1
                        self.vy = 0
                    next_py = self.py
                    break

        self.py = next_py

        # Movimiento X
        next_px = self.px + self.vx
        player_rect = [next_px + 2, self.py, next_px + 14, self.py + 24]
        blocked_x = False
        
        for y in range(int(player_rect[1]//BLOCK_SIZE), int(player_rect[3]//BLOCK_SIZE) + 1):
            for x in range(int(player_rect[0]//BLOCK_SIZE), int(player_rect[2]//BLOCK_SIZE) + 1):
                if self.is_solid(x, y):
                    if self.vx > 0:
                        self.px = x * BLOCK_SIZE - 14.1
                        self.vx = 0
                    elif self.vx < 0:
                        self.px = (x + 1) * BLOCK_SIZE - 2.1
                        self.vx = 0
                    blocked_x = True
                    next_px = self.px
                    break
        
        self.px = next_px

        # Anti-Stuck System
        if abs(self.px - self.last_px) < 0.1 and abs(self.py - self.last_py) < 0.1 and self.task_queue:
            self.stuck_timer += 1
            if self.stuck_timer > 90: # 3 segundos atascado
                print("IA ATASCADA! Reseteando tarea actual y cavando alrededor.")
                self.stuck_timer = 0
                self.task_queue.pop(0) # Abortar tarea
                # Minar todo alrededor para desatascarse
                cbx, cby = int(self.px // BLOCK_SIZE), int(self.py // BLOCK_SIZE)
                self.task_queue.insert(0, ('MINE', cbx + self.facing, cby))
                self.task_queue.insert(0, ('MINE', cbx + self.facing, cby - 1))
        else:
            self.stuck_timer = 0
            
        self.last_px = self.px
        self.last_py = self.py

        # CEREBRO A* (Orientado a Tareas)
        if self.action_timer > 0:
            self.action_timer -= 1
            return # Ejecutando animación
            
        bx = int(self.px // BLOCK_SIZE)
        by = int(self.py // BLOCK_SIZE)
        
        if not self.task_queue:
            self.vx = 0
            if self.macro_goal == 'GATHER_WOOD':
                if self.inventory[WOOD] >= 20:
                    self.inventory[PLANKS] += self.inventory[WOOD] * 2
                    self.inventory[WOOD] = 0
                    self.macro_goal = 'BUILD_BASE'
                else:
                    # Buscar madera cercana
                    found = False
                    for sx in range(bx - 30, bx + 30):
                        for sy in range(by - 20, by + 10):
                            if self.world.get((sx, sy), AIR) == WOOD:
                                self.task_queue.append(('MINE', sx, sy))
                                found = True
                                break
                        if found: break
                    if not found:
                        self.task_queue.append(('WALK', bx + random.choice([-10, 10]), by))
                        
            elif self.macro_goal == 'BUILD_BASE':
                self.plan_base()
                self.macro_goal = 'EXPLORE_DEEP'
                
            elif self.macro_goal == 'EXPLORE_DEEP':
                # Excavar hacia abajo a la derecha
                self.task_queue.append(('MINE', bx + 1, by))
                self.task_queue.append(('MINE', bx + 1, by + 1))
                self.task_queue.append(('WALK', bx + 1, by + 1))
                if random.random() < 0.1:
                    self.task_queue.append(('PLACE', bx, by - 1, TORCH))

        if self.task_queue:
            task = self.task_queue[0]
            action = task[0]
            tx, ty = task[1], task[2]
            
            dist = math.hypot(tx - bx, ty - by)
            dx = tx - bx
            
            # Si estamos a punto de llegar a un objetivo pero DX es 0 y nos atascamos
            if dx == 0 and dist > 3 and blocked_x:
                self.facing = random.choice([-1, 1])
                self.vx = 2.5 * self.facing
            
            if action == 'MINE' or action == 'PLACE':
                if dist <= 3:
                    if action == 'MINE':
                        b = self.world.get((tx, ty), AIR)
                        if b in self.inventory: self.inventory[b] += 1
                        self.set_block(tx, ty, AIR)
                    else:
                        block_id = task[3]
                        if self.inventory.get(block_id, 0) > 0 and self.world.get((tx, ty), AIR) == AIR:
                            self.set_block(tx, ty, block_id)
                            self.inventory[block_id] -= 1
                    self.task_queue.pop(0)
                    self.action_timer = 10
                    self.vx = 0
                    self.facing = 1 if tx > bx else -1
                else:
                    # Caminar hacia allí
                    dx = tx - bx
                    self.facing = 1 if dx > 0 else -1
                    self.vx = 2.5 * self.facing
                    if blocked_x and on_ground:
                        front_x = bx + self.facing
                        head_solid = self.is_solid(front_x, by - 1)
                        foot_solid = self.is_solid(front_x, by)
                        
                        if head_solid:
                            self.task_queue.insert(0, ('MINE', front_x, by - 1))
                            self.vx = 0
                        elif foot_solid:
                            if self.is_solid(front_x, by - 2): # Techo bloqueado, picar abajo
                                self.task_queue.insert(0, ('MINE', front_x, by))
                                self.vx = 0
                            else:
                                self.vy = -8.5 # Salto limpio
                            
            elif action == 'WALK':
                dx = tx - bx
                if abs(dx) <= 1:
                    self.task_queue.pop(0)
                    self.vx = 0
                else:
                    self.facing = 1 if dx > 0 else -1
                    self.vx = 2.5 * self.facing
                    if blocked_x and on_ground:
                        front_x = bx + self.facing
                        head_solid = self.is_solid(front_x, by - 1)
                        foot_solid = self.is_solid(front_x, by)
                        
                        if head_solid:
                            self.task_queue.insert(0, ('MINE', front_x, by - 1))
                            self.vx = 0
                        elif foot_solid:
                            if self.is_solid(front_x, by - 2): # Techo tapado, no saltar
                                self.task_queue.insert(0, ('MINE', front_x, by))
                                self.vx = 0
                            else:
                                self.vy = -8.5 # Salto limpio

    def get_frame(self):
        self.update()
        target_cam_y = int(self.py) - SCREEN_H // 2 + 50
        if not hasattr(self, 'cam_y'): self.cam_y = target_cam_y
        self.cam_y += (target_cam_y - self.cam_y) * 0.2
        
        target_cam_x = int(self.px) - SCREEN_W // 2
        if not hasattr(self, 'cam_x'): self.cam_x = target_cam_x
        self.cam_x += (target_cam_x - self.cam_x) * 0.2
        
        cam_x = int(self.cam_x)
        cam_y = int(self.cam_y)
        
        frame = Image.new('RGB', (SCREEN_W, SCREEN_H), (135, 206, 235))
        
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
        
        light_map = {}
        for bx in range(cam_bx - 1, cam_bx + BLOCKS_W + 2):
            sky_light = 15 if not (1000 < self.time_of_day < 2400) else 4
            for by in range(0, cam_by + BLOCKS_H + 2):
                if self.is_solid(bx, by): sky_light = 0
                light_map[(bx, by)] = sky_light
                
        for (tx, ty) in self.torches:
            if cam_bx - 2 < tx < cam_bx + BLOCKS_W + 2 and cam_by - 2 < ty < cam_by + BLOCKS_H + 2:
                light_map[(tx, ty)] = 15
                
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
                
                l = light_map.get((bx, by), 0)
                if l < 15:
                    frame.paste(self.dark_overlays[l], (sx, sy), self.dark_overlays[l])

        # Jugador
        draw = ImageDraw.Draw(frame)
        rx = int(self.px) - cam_x
        ry = int(self.py) - cam_y
        draw.rectangle([rx+2, ry+8, rx+14, ry+16], fill=(0, 200, 200)) # Camisa
        draw.rectangle([rx+4, ry+16, rx+12, ry+24], fill=(0, 0, 200)) # Pantalones
        draw.rectangle([rx+4, ry, rx+12, ry+8], fill=(255, 200, 150)) # Cabeza
        ex = rx+9 if self.facing == 1 else rx+6
        draw.rectangle([ex, ry+2, ex+1, ry+3], fill=(0,0,0))
        
        if self.action_timer > 0 and self.task_queue:
            t = self.task_queue[0]
            if t[0] == 'MINE':
                tx = t[1] * BLOCK_SIZE - cam_x
                ty = t[2] * BLOCK_SIZE - cam_y
                draw.line([rx+8, ry+12, tx+8, ty+8], fill=(139,69,19), width=2)
            
        hud_y = SCREEN_H - 40
        draw.rectangle([0, hud_y, SCREEN_W, SCREEN_H], fill=(50, 50, 50, 200))
        items = [(WOOD, "Madera"), (PLANKS, "Tablones"), (STONE, "Piedra"), (COAL, "Carbon"), (DIAMOND, "Diamante"), (TORCH, "Antorchas")]
        for i, (b_id, name) in enumerate(items):
            x = 10 + i * 70
            if b_id == TORCH:
                frame.paste(self.textures[DIRT], (x, hud_y + 10))
                frame.paste(self.textures[TORCH], (x, hud_y + 10), self.textures[TORCH])
            else:
                frame.paste(self.textures[b_id], (x, hud_y + 10))
            qty = self.inventory.get(b_id, 0)
            draw.text((x + 20, hud_y + 12), f"x{qty}", fill=(255,255,255))
            
        # IA DEBUG HUD
        draw.rectangle([0, 0, 250, 80], fill=(0, 0, 0, 180))
        draw.text((5, 5), f"PENSAMIENTO IA:", fill=(0,255,0))
        draw.text((5, 20), f"META: {self.macro_goal}", fill=(255,255,255))
        current_task = str(self.task_queue[0]) if self.task_queue else "IDLE"
        draw.text((5, 35), f"TAREA: {current_task}", fill=(255,255,255))
        draw.text((5, 50), f"COORD: X={int(self.px//BLOCK_SIZE)} Y={int(self.py//BLOCK_SIZE)}", fill=(255,255,255))
        if self.stuck_timer > 30:
            draw.text((5, 65), f"! ATASCADO ! ({self.stuck_timer}/90)", fill=(255,0,0))

        return frame

    def start(self): self.running = True
    def stop(self): self.running = False
