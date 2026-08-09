import os
import json
import random
from PIL import Image, ImageDraw

class ShimejiEngine:
    def __init__(self, size=(480, 480), fps=30):
        self.size = size
        self.width, self.height = size
        self.fps = fps
        self.running = False
        
        self.assets_dir = os.path.join(os.path.dirname(__file__), 'assets', 'shimeji', 'miku')
        
        # Load sprites
        self.sprites = {
            'idle': self.load_asset('idle', 'idle.png', 'idle.json'),
            'walk_left': self.load_asset('walk_left', 'walk_left.png', 'walk.json'),
            'walk_right': self.load_asset('walk_right', 'walk_right.png', 'walk.json')
        }
        
        # Upscale sprites by 2x for the 480x480 screen so it's not too tiny
        for state in self.sprites:
            self.sprites[state] = [img.resize((img.width * 2, img.height * 2), Image.NEAREST) for img in self.sprites[state]]
            
        self.state = 'idle'
        self.frame_idx = 0
        self.frame_timer = 0
        self.frame_duration = 3 # 3 ticks per frame at 30fps = 10fps animation
        
        # Character state
        self.sprite_w = self.sprites['idle'][0].width
        self.sprite_h = self.sprites['idle'][0].height
        self.x = self.width // 2 - self.sprite_w // 2
        self.y = self.height - self.sprite_h - 40
        self.vx = 0
        
        self.state_timer = 60

    def load_asset(self, name, default_png, default_json):
        gif_path = os.path.join(self.assets_dir, f"{name}.gif")
        if os.path.exists(gif_path):
            from PIL import ImageSequence
            img = Image.open(gif_path)
            frames = []
            for frame in ImageSequence.Iterator(img):
                f = frame.copy().convert('RGBA')
                frames.append(f)
            return frames if frames else [Image.new('RGBA', (64, 100), (255, 0, 0, 255))]
            
        return self.load_spritesheet(default_png, default_json)

    def load_spritesheet(self, image_file, json_file):
        img_path = os.path.join(self.assets_dir, image_file)
        json_path = os.path.join(self.assets_dir, json_file)
        
        if not os.path.exists(img_path) or not os.path.exists(json_path):
            img = Image.new('RGBA', (64, 100), (255, 0, 0, 255))
            return [img]
            
        sheet = Image.open(img_path).convert("RGBA")
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        frames = []
        for frame_name, frame_data in data['frames'].items():
            rect = frame_data['frame']
            box = (rect['x'], rect['y'], rect['x'] + rect['w'], rect['y'] + rect['h'])
            frame_img = sheet.crop(box)
            frames.append(frame_img)
            
        return frames

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def update(self):
        self.state_timer -= 1
        
        if self.state_timer <= 0:
            # Pick a new state
            choices = ['idle', 'walk_left', 'walk_right']
            self.state = random.choice(choices)
            if self.state == 'idle':
                self.state_timer = random.randint(60, 150)
                self.vx = 0
            elif self.state == 'walk_left':
                self.state_timer = random.randint(30, 90)
                self.vx = -4
            elif self.state == 'walk_right':
                self.state_timer = random.randint(30, 90)
                self.vx = 4
                
            self.frame_idx = 0
            
        # Move
        self.x += self.vx
        
        # Bounds check
        if self.x < 20:
            self.x = 20
            self.state = 'walk_right'
            self.vx = 4
            self.state_timer = random.randint(30, 90)
        elif self.x + self.sprite_w > self.width - 20:
            self.x = self.width - 20 - self.sprite_w
            self.state = 'walk_left'
            self.vx = -4
            self.state_timer = random.randint(30, 90)
            
        # Animation
        self.frame_timer += 1
        if self.frame_timer >= self.frame_duration:
            self.frame_timer = 0
            self.frame_idx = (self.frame_idx + 1) % len(self.sprites[self.state])

    def get_frame(self):
        self.update()
        
        # Draw background (a cute room or gradient)
        img = Image.new('RGB', self.size, (240, 248, 255)) # Alice Blue
        draw = ImageDraw.Draw(img)
        
        # Draw a floor
        floor_y = self.height - 40
        draw.rectangle([0, floor_y, self.width, self.height], fill=(200, 220, 240))
        
        # Draw the character
        sprite = self.sprites[self.state][self.frame_idx]
        img.paste(sprite, (int(self.x), int(self.y)), mask=sprite)
        
        return img
