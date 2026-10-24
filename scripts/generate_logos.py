import os
from PIL import Image, ImageDraw, ImageFont

public_dir = r'C:\Users\sagar\Desktop\Project\anydownloader\public'
os.makedirs(public_dir, exist_ok=True)

# 1. SVG Logo
svg_content = '''<svg xmlns=http://www.w3.org/2000/svg viewBox=0 0 512 512 width=512 height=512>
  <defs>
    <linearGradient id=ovdBg x1=0% y1=0% x2=100% y2=100%>
      <stop offset=0% stop-color=#0F172A />
      <stop offset=100% stop-color=#020617 />
    </linearGradient>
    <linearGradient id=blueG x1=0% y1=0% x2=100% y2=100%>
      <stop offset=0% stop-color=#60A5FA />
      <stop offset=100% stop-color=#2563EB />
    </linearGradient>
  </defs>
  
  <rect x=16 y=16 width=480 height=480 rx=108 fill=url(#ovdBg) stroke=#1E293B stroke-width=8 />
  <rect x=28 y=28 width=456 height=456 rx=96 fill=none stroke=rgba(255,255,255,0.06) stroke-width=3 />
  
  <g transform=translate(256, 190)>
    <text text-anchor=middle font-family=-apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif font-weight=900 font-size=124 fill=#FFFFFF letter-spacing=4>OVD</text>
  </g>
  
  <g transform=translate(256, 320)>
    <rect x=-8 y=-60 width=16 height=55 rx=8 fill=url(#blueG) />
    <path d=M-36 -10 L0 28 L36 -10 Z fill=url(#blueG) />
    <path d=M-70 28 L-70 48 C-70 56 -64 62 -56 62 L56 62 C64 62 70 56 70 48 L70 28 fill=none stroke=#FFFFFF stroke-width=12 stroke-linecap=round stroke-linejoin=round />
  </g>
  
  <g transform=translate(256, 440)>
    <text text-anchor=middle font-family=-apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif font-weight=700 font-size=24 fill=#94A3B8 letter-spacing=6>DOWNLOADER</text>
  </g>
</svg>'''

with open(os.path.join(public_dir, 'logo.svg'), 'w', encoding='utf-8') as f:
    f.write(svg_content)

with open(os.path.join(public_dir, 'favicon.svg'), 'w', encoding='utf-8') as f:
    f.write(svg_content)

print(SVGs created.)

# 2. 512x512 PNG Logo
img = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Outer box
draw.rounded_rectangle([(16, 16), (496, 496)], radius=108, fill=(15, 23, 42, 255), outline=(30, 41, 59, 255), width=8)
draw.rounded_rectangle([(28, 28), (484, 484)], radius=96, fill=None, outline=(255, 255, 255, 18), width=3)

# Fonts
try:
    font_main = ImageFont.truetype('arialbd.ttf', 115)
    font_sub = ImageFont.truetype('arialbd.ttf', 24)
except Exception:
    font_main = ImageFont.load_default()
    font_sub = ImageFont.load_default()

draw.text((256, 175), OVD, font=font_main, fill=(255, 255, 255, 255), anchor=mm)

# Arrow & Tray
arrow_color = (37, 99, 235, 255)
white = (255, 255, 255, 255)

# Tray
draw.line([(186, 350), (186, 385), (326, 385), (326, 350)], fill=white, width=12, joint=curve)
# Arrow stem
draw.rounded_rectangle([(248, 260), (264, 320)], radius=8, fill=arrow_color)
# Arrow head
draw.polygon([(220, 315), (256, 355), (292, 315)], fill=arrow_color)

# Subtitle
draw.text((256, 440), DOWNLOADER, font=font_sub, fill=(148, 163, 184, 255), anchor=mm)

img.save(os.path.join(public_dir, 'logo.png'), 'PNG')
img.resize((180, 180), Image.Resampling.LANCZOS).save(os.path.join(public_dir, 'apple-touch-icon.png'), 'PNG')
img.resize((32, 32), Image.Resampling.LANCZOS).save(os.path.join(public_dir, 'favicon-32x32.png'), 'PNG')
print(PNGs created.)
