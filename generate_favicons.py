import os
from PIL import Image, ImageDraw

def create_base_image():
    # 512x512 transparent canvas
    img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    
    # Create mask for rounded rectangle
    mask = Image.new("L", (512, 512), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([20, 20, 492, 492], radius=100, fill=255)
    
    # Create gradient background
    grad = Image.new("RGBA", (512, 512))
    draw_grad = ImageDraw.Draw(grad)
    # Draw gradient from #6366f1 (99, 102, 241) to #4f46e5 (79, 70, 229)
    for y in range(512):
        r = int(99 + (79 - 99) * y / 512)
        g = int(102 + (70 - 102) * y / 512)
        b = int(241 + (229 - 241) * y / 512)
        draw_grad.line([(0, y), (512, y)], fill=(r, g, b, 255))
        
    # Apply mask
    bg = Image.composite(grad, Image.new("RGBA", (512, 512), (0, 0, 0, 0)), mask)
    
    # Draw the letter "F" on top in white
    draw = ImageDraw.Draw(bg)
    
    # Vertical stem: x from 170 to 230, y from 130 to 390
    draw.rounded_rectangle([170, 130, 230, 390], radius=8, fill=(255, 255, 255, 255))
    
    # Top horizontal bar: x from 230 to 350, y from 130 to 190
    draw.rounded_rectangle([230, 130, 350, 190], radius=8, fill=(255, 255, 255, 255))
    
    # Middle horizontal bar: x from 230 to 310, y from 245 to 305
    draw.rounded_rectangle([230, 245, 310, 305], radius=8, fill=(255, 255, 255, 255))
    
    # Cute yellow accent dot for kids style
    draw.ellipse([360, 130, 400, 170], fill=(251, 191, 36, 255))
    
    return bg

def generate():
    base = create_base_image()
    
    # 1. Save favicon.ico
    base.save("favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    print("Saved favicon.ico")
    
    # 2. Save favicon-96x96.png
    base.resize((96, 96), Image.Resampling.LANCZOS).save("favicon-96x96.png", format="PNG")
    print("Saved favicon-96x96.png")
    
    # 3. Save apple-touch-icon.png (180x180)
    base.resize((180, 180), Image.Resampling.LANCZOS).save("apple-touch-icon.png", format="PNG")
    print("Saved apple-touch-icon.png")
    
    # 4. Save web-app-manifest-192x192.png
    base.resize((192, 192), Image.Resampling.LANCZOS).save("web-app-manifest-192x192.png", format="PNG")
    print("Saved web-app-manifest-192x192.png")
    
    # 5. Save web-app-manifest-512x512.png
    base.save("web-app-manifest-512x512.png", format="PNG")
    print("Saved web-app-manifest-512x512.png")

if __name__ == "__main__":
    generate()
