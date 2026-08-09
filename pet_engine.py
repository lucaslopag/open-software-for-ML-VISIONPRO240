import time
import math
import random
from PIL import Image, ImageDraw, ImageFont
import datetime

class PetEngine:
    def __init__(self, size=(480, 480), fps=30):
        self.size = size
        self.width, self.height = size
        self.fps = fps
        self.running = False
        
        # Pet state
        self.radius = 60
        self.x = self.width / 2
        self.y = self.height / 2
        self.vx = 6.0
        self.vy = 4.0
        
        # Colors
        self.color_body = (0, 255, 170) # Cyberpunk cyan/green
        self.color_bg = (15, 15, 20)
        self.color_bg_sleep = (5, 5, 15)
        
        self.blink_timer = 0
        self.is_blinking = False
        self.sleep_mode = False

        self.particles = []

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def update(self):
        # Check time for sleep mode (23:00 to 07:00)
        hour = datetime.datetime.now().hour
        self.sleep_mode = (hour >= 23 or hour < 7)

        if self.sleep_mode:
            # Move slowly to bottom center and stay there
            target_x = self.width / 2
            target_y = self.height - self.radius - 20
            self.x += (target_x - self.x) * 0.05
            self.y += (target_y - self.y) * 0.05
            
            # Spawn Zzz particles
            if random.random() < 0.03:
                self.particles.append({
                    'x': self.x + random.randint(-30, 30),
                    'y': self.y - self.radius,
                    'vy': -random.uniform(1.0, 2.5),
                    'life': 255,
                    'text': 'Z'
                })
        else:
            # Bounce around
            self.x += self.vx
            self.y += self.vy

            # Add gravity/wobble effect randomly
            if random.random() < 0.01:
                self.vx += random.uniform(-2, 2)
                self.vy += random.uniform(-2, 2)
                
            # Speed limits
            speed = math.hypot(self.vx, self.vy)
            if speed > 10:
                self.vx = (self.vx / speed) * 10
                self.vy = (self.vy / speed) * 10
            elif speed < 3:
                self.vx *= 1.1
                self.vy *= 1.1

            # Collision with walls
            margin = self.radius
            if self.x - margin < 0:
                self.x = margin
                self.vx = abs(self.vx)
            elif self.x + margin > self.width:
                self.x = self.width - margin
                self.vx = -abs(self.vx)
                
            if self.y - margin < 0:
                self.y = margin
                self.vy = abs(self.vy)
            elif self.y + margin > self.height:
                self.y = self.height - margin
                self.vy = -abs(self.vy)

        # Update blink
        if self.blink_timer > 0:
            self.blink_timer -= 1
            if self.blink_timer == 0:
                self.is_blinking = False
        elif random.random() < 0.02:
            self.is_blinking = True
            self.blink_timer = random.randint(3, 8)

        # Update particles
        for p in self.particles:
            p['y'] += p['vy']
            p['life'] -= 4
        self.particles = [p for p in self.particles if p['life'] > 0]

    def get_frame(self):
        self.update()
        
        bg_color = self.color_bg_sleep if self.sleep_mode else self.color_bg
        img = Image.new('RGB', self.size, bg_color)
        draw = ImageDraw.Draw(img)

        # Draw grid background
        if not self.sleep_mode:
            for i in range(0, self.width, 40):
                draw.line([(i, 0), (i, self.height)], fill=(30, 30, 40), width=1)
                draw.line([(0, i), (self.width, i)], fill=(30, 30, 40), width=1)

        # Draw Pet Body
        bbox = [self.x - self.radius, self.y - self.radius, self.x + self.radius, self.y + self.radius]
        draw.ellipse(bbox, fill=self.color_body)
        
        # Draw highlights (glassy effect)
        hl_bbox = [self.x - self.radius*0.6, self.y - self.radius*0.8, self.x + self.radius*0.2, self.y - self.radius*0.2]
        draw.ellipse(hl_bbox, fill=(255, 255, 255, 100))

        # Draw Eyes
        eye_offset_x = (self.vx / 10.0) * 15 if not self.sleep_mode else 0
        eye_offset_y = (self.vy / 10.0) * 15 if not self.sleep_mode else 0
        
        eye_y = self.y - 10 + eye_offset_y
        left_eye_x = self.x - 20 + eye_offset_x
        right_eye_x = self.x + 20 + eye_offset_x

        if self.sleep_mode or self.is_blinking:
            # Closed eyes (lines)
            draw.line([(left_eye_x-12, eye_y), (left_eye_x+12, eye_y)], fill=(0,0,0), width=6)
            draw.line([(right_eye_x-12, eye_y), (right_eye_x+12, eye_y)], fill=(0,0,0), width=6)
        else:
            # Open eyes
            draw.ellipse([left_eye_x-12, eye_y-12, left_eye_x+12, eye_y+12], fill=(255,255,255))
            draw.ellipse([right_eye_x-12, eye_y-12, right_eye_x+12, eye_y+12], fill=(255,255,255))
            # Pupils
            draw.ellipse([left_eye_x-5, eye_y-5, left_eye_x+5, eye_y+5], fill=(0,0,0))
            draw.ellipse([right_eye_x-5, eye_y-5, right_eye_x+5, eye_y+5], fill=(0,0,0))

        # Draw Particles
        for p in self.particles:
            c = max(0, min(255, int(p['life'])))
            draw.text((p['x'], p['y']), p.get('text', ''), fill=(c, c, c))

        return img
