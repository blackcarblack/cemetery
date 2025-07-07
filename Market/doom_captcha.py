import random
import string
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from django.core.cache import cache
from django.conf import settings

class DoomCaptcha:
    def __init__(self):
        self.width = 300
        self.height = 100
        self.font_size = 30
        self.code_length = 6
        self.cache_timeout = 300  # 5 minutes
        self.bg_color = (0, 0, 0)  # Black background like DOOM
        self.text_colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
        ]
        
    def generate_code(self):
        """Generate a random alphanumeric code."""
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(self.code_length))
    
    def create_noise(self, draw):
        """Create noise in the background like DOOM's visual style."""
        # Draw random lines
        for _ in range(8):
            x1 = random.randint(0, self.width)
            y1 = random.randint(0, self.height)
            x2 = random.randint(0, self.width)
            y2 = random.randint(0, self.height)
            draw.line([(x1, y1), (x2, y2)], fill=random.choice(self.text_colors), width=1)
        
        # Draw random points
        for _ in range(100):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            draw.point((x, y), fill=random.choice(self.text_colors))
    
    def generate_image(self, code):
        """Generate a DOOM-style CAPTCHA image."""
        # Create a new image with black background
        image = Image.new('RGB', (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(image)
        
        # Add noise
        self.create_noise(draw)
        
        # Load a pixelated font (use a default font if not available)
        try:
            font = ImageFont.truetype("fonts/Doom.ttf", self.font_size)
        except IOError:
            font = ImageFont.load_default()
        
        # Draw each character with a different color and slight rotation
        x = 20
        for i, char in enumerate(code):
            # Choose a random color for each character
            color = random.choice(self.text_colors)
            
            # Create a new image for each character to apply rotation
            char_img = Image.new('RGBA', (self.font_size, self.font_size), (0, 0, 0, 0))
            char_draw = ImageDraw.Draw(char_img)
            char_draw.text((0, 0), char, font=font, fill=color)
            
            # Rotate the character slightly
            rotated_char = char_img.rotate(random.randint(-15, 15), expand=1)
            
            # Paste the rotated character onto the main image
            image.paste(rotated_char, (x, random.randint(10, 30)), rotated_char)
            x += self.font_size + 5
        
        # Apply a slight blur to make it look more like DOOM's aesthetic
        image = image.filter(ImageFilter.GaussianBlur(radius=0.8))
        
        return image
    
    def get_captcha(self):
        """Generate a new CAPTCHA and return the image and code."""
        code = self.generate_code()
        image = self.generate_image(code)
        
        # Save the code in the session with a unique key
        cache_key = f'doom_captcha_{code}'
        cache.set(cache_key, code, self.cache_timeout)
        
        # Convert image to bytes
        img_io = BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)
        
        return img_io, code
    
    def validate_captcha(self, user_input, captcha_code):
        """Validate the user's input against the CAPTCHA."""
        cache_key = f'doom_captcha_{captcha_code}'
        stored_code = cache.get(cache_key)
        
        # Delete the used CAPTCHA
        if stored_code:
            cache.delete(cache_key)
        
        return user_input.upper() == stored_code
