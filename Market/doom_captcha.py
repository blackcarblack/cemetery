import random
import string
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from django.core.cache import cache
from django.conf import settings

class DoomCaptcha:
   
    def __init__(self):
        self.width = 480
        self.height = 320
        self.monsters_to_kill = 3
        self.cache_timeout = 300  # 5 minutes
        
       
        self.doom_palette = [
            # Classic DOOM red spectrum (blood, demons, fire)
            (0, 0, 0),        # Pure black (void)
            (64, 0, 0),       # Dark red
            (128, 0, 0),      # Medium red  
            (192, 0, 0),      # Bright red
            (255, 0, 0),      # Blood red
            (255, 64, 0),     # Red-orange
            (255, 128, 0),    # Orange (fire)
            (255, 192, 0),    # Light orange
            (255, 255, 0),    # Yellow (muzzle flash)
            
            # DOOM green spectrum (radiation, slime, armor)
            (0, 64, 0),       # Dark green
            (0, 128, 0),      # Medium green
            (0, 192, 0),      # Bright green
            (0, 255, 0),      # Neon green
            (64, 255, 64),    # Light green
            
            # DOOM brown spectrum (walls, dirt, textures)
            (64, 32, 16),     # Dark brown
            (128, 64, 32),    # Medium brown
            (192, 96, 48),    # Light brown
            (160, 82, 45),    # Saddle brown
            (139, 69, 19),    # Classic brown
            
            # DOOM gray spectrum (metal, concrete)
            (32, 32, 32),     # Dark gray
            (64, 64, 64),     # Medium gray
            (128, 128, 128),  # Gray
            (192, 192, 192),  # Light gray
            (255, 255, 255),  # White (highlights)
            
            # DOOM blue spectrum (tech, computers)
            (0, 0, 128),      # Navy blue
            (64, 64, 255),    # Medium blue
            (128, 128, 255),  # Light blue
        ]
        
        # Doom monster symbols (ASCII art style)
        self.doom_monsters = [
            "?", "?", "?", "?", "?", "?", "?", "?"
        ]
        
        # Game state tracking
        self.killed_monsters = 0
        
    def generate_game_session(self):
        """Generate a unique game session ID."""
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(8))
    
    def create_doom_environment(self, draw):
        """Create DOOM 1993-style game environment."""
        # Draw floor (classic DOOM brown/gray pattern)
        floor_y = int(self.height * 0.7)
        for y in range(floor_y, self.height):
            # Create floor texture with horizontal lines
            if y % 4 == 0:
                draw.line([(0, y), (self.width, y)], fill=(64, 32, 16), width=1)
        
        # Draw walls/corridors (DOOM-style perspective)
        wall_color = (128, 64, 32)
        # Left wall
        for x in range(0, 60):
            color_shade = max(32, wall_color[0] - x)
            draw.line([(x, 0), (x, floor_y)], fill=(color_shade, color_shade//2, color_shade//4))
        
        # Right wall  
        for x in range(self.width-60, self.width):
            color_shade = max(32, wall_color[0] - (self.width - x))
            draw.line([(x, 0), (x, floor_y)], fill=(color_shade, color_shade//2, color_shade//4))
        
        # Add DOOM-style lighting effects
        self.add_doom_lighting(draw)
        
        # Add scan lines for CRT effect
        for y in range(0, self.height, 3):
            draw.line([(0, y), (self.width, y)], fill=(16, 16, 16), width=1)
    
    def add_doom_lighting(self, draw):
        """Add DOOM-style lighting and atmosphere."""
        # Add flickering light effects
        for _ in range(10):
            x = random.randint(0, self.width)
            y = random.randint(0, int(self.height * 0.7))
            # Create light spots
            for radius in range(1, 20, 3):
                alpha = max(0, 50 - radius * 3)
                color = (255, 255, 0, alpha)  # Yellow light
                # Simple circle approximation
                for angle in range(0, 360, 45):
                    import math
                    px = x + int(radius * math.cos(math.radians(angle)))
                    py = y + int(radius * math.sin(math.radians(angle)))
                    if 0 <= px < self.width and 0 <= py < self.height:
                        draw.point((px, py), fill=(255, 255, 0))
        
        # Add atmospheric particles
        for _ in range(50):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            color = random.choice([(64, 0, 0), (32, 32, 0), (0, 32, 0)])
            draw.point((x, y), fill=color)
    
    def draw_monsters(self, draw, session_id):
        """Draw DOOM monsters on the game field."""
        monsters_positions = []
        
        # Draw 3 monsters that need to be killed
        for i in range(3):
            # Random positions on the floor area
            x = random.randint(80, self.width - 80)
            y = random.randint(int(self.height * 0.5), int(self.height * 0.65))
            
            # Choose random monster symbol
            monster = random.choice(self.doom_monsters)
            monster_color = random.choice([
                (255, 0, 0),      # Red demon
                (255, 128, 0),    # Orange fire demon
                (128, 0, 128),    # Purple baron
                (0, 255, 0),      # Green monster
            ])
            
            # Draw monster with outline for visibility
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except IOError:
                font = ImageFont.load_default()
            
            # Draw outline
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx != 0 or dy != 0:
                        draw.text((x+dx, y+dy), monster, font=font, fill=(0, 0, 0))
            
            # Draw monster
            draw.text((x, y), monster, font=font, fill=monster_color)
            
            monsters_positions.append((x, y, monster))
        
        # Store monster positions in cache for validation
        cache.set(f'doom_monsters_{session_id}', monsters_positions, self.cache_timeout)
        
        return monsters_positions
    
    def draw_crosshair(self, draw):
        """Draw DOOM-style crosshair in center."""
        center_x, center_y = self.width // 2, self.height // 2
        crosshair_size = 15
        crosshair_color = (255, 255, 0)  # Yellow
        
        # Horizontal line
        draw.line([
            (center_x - crosshair_size, center_y),
            (center_x + crosshair_size, center_y)
        ], fill=crosshair_color, width=2)
        
        # Vertical line
        draw.line([
            (center_x, center_y - crosshair_size),
            (center_x, center_y + crosshair_size)
        ], fill=crosshair_color, width=2)

    def generate_image(self, session_id):
        """Generate a DOOM-style game CAPTCHA image."""
        # Create a new image with black background
        image = Image.new('RGB', (self.width, self.height), (0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Create DOOM environment
        self.create_doom_environment(draw)
        
        # Draw monsters
        self.draw_monsters(draw, session_id)
        
        # Draw crosshair
        self.draw_crosshair(draw)
        
        # Add instruction text
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except IOError:
            font = ImageFont.load_default()
            
        instruction = "Kill 3 monsters to prove you're human!"
        draw.text((10, 10), instruction, font=font, fill=(255, 255, 255))
        
        # Add game status
        status = f"Monsters killed: {self.killed_monsters}/3"
        draw.text((10, self.height - 30), status, font=font, fill=(255, 255, 0))
        
        return image
    
    def get_captcha(self):
        """Generate a new DOOM game CAPTCHA and return the image and session ID."""
        session_id = self.generate_game_session()
        image = self.generate_image(session_id)
        
        # Initialize game state in cache
        cache.set(f'doom_game_state_{session_id}', {
            'monsters_killed': 0,
            'total_monsters': 3,
            'completed': False
        }, self.cache_timeout)
        
        # Convert image to bytes
        img_io = BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)
        
        return img_io, session_id
    
    def validate_captcha(self, user_clicks, session_id):
        """Validate the user's monster kills against the CAPTCHA."""
        # Get game state
        game_state = cache.get(f'doom_game_state_{session_id}')
        if not game_state:
            return False
            
        # Get monster positions
        monsters = cache.get(f'doom_monsters_{session_id}')
        if not monsters:
            return False
        
        # Count successful monster kills based on click positions
        killed_count = 0
        for click_x, click_y in user_clicks:
            for monster_x, monster_y, monster_symbol in monsters:
                # Check if click is close enough to monster (within 30 pixels)
                distance = ((click_x - monster_x) ** 2 + (click_y - monster_y) ** 2) ** 0.5
                if distance <= 30:
                    killed_count += 1
                    break
        
        # Update game state
        game_state['monsters_killed'] = killed_count
        game_state['completed'] = killed_count >= 3
        
        # Clean up cache if completed
        if game_state['completed']:
            cache.delete(f'doom_game_state_{session_id}')
            cache.delete(f'doom_monsters_{session_id}')
        else:
            cache.set(f'doom_game_state_{session_id}', game_state, self.cache_timeout)
        
        return game_state['completed']
    
    def get_game_state(self, session_id):
        """Get current game state."""
        return cache.get(f'doom_game_state_{session_id}', {
            'monsters_killed': 0,
            'total_monsters': 3,
            'completed': False
        })
