import os
from PIL import Image, ImageDraw

def generate_icons():
    src_icon = os.path.abspath("miku_ui/src/assets/icon_link.png")
    if not os.path.exists(src_icon):
        print(f"Error: {src_icon} not found")
        return

    base_img = Image.open(src_icon).convert("RGBA")
    res_dir = os.path.abspath("miku_android/app/src/main/res")
    
    densities = {
        "mipmap-mdpi": (48, 108),
        "mipmap-hdpi": (72, 162),
        "mipmap-xhdpi": (96, 216),
        "mipmap-xxhdpi": (144, 324),
        "mipmap-xxxhdpi": (192, 432)
    }

    for folder, (launcher_sz, fore_sz) in densities.items():
        folder_path = os.path.join(res_dir, folder)
        os.makedirs(folder_path, exist_ok=True)

        # 1. Standard ic_launcher
        launcher_img = base_img.resize((launcher_sz, launcher_sz), Image.Resampling.LANCZOS)
        launcher_img.save(os.path.join(folder_path, "ic_launcher.png"), "PNG")

        # 2. Round ic_launcher_round
        round_img = Image.new("RGBA", (launcher_sz, launcher_sz), (0, 0, 0, 0))
        mask = Image.new("L", (launcher_sz, launcher_sz), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, launcher_sz, launcher_sz), fill=255)
        round_img.paste(launcher_img, (0, 0), mask)
        round_img.save(os.path.join(folder_path, "ic_launcher_round.png"), "PNG")

        # 3. Adaptive foreground (108dp canvas with ~72dp icon in center to avoid clipping)
        fg_canvas = Image.new("RGBA", (fore_sz, fore_sz), (0, 0, 0, 0))
        inner_sz = int(fore_sz * 0.72)
        inner_img = base_img.resize((inner_sz, inner_sz), Image.Resampling.LANCZOS)
        offset = (fore_sz - inner_sz) // 2
        fg_canvas.paste(inner_img, (offset, offset), inner_img)
        fg_canvas.save(os.path.join(folder_path, "ic_launcher_foreground.png"), "PNG")

        print(f"Generated icons for {folder} ({launcher_sz}x{launcher_sz}, fg: {fore_sz}x{fore_sz})")

    # Update background color in values/ic_launcher_background.xml
    values_dir = os.path.join(res_dir, "values")
    os.makedirs(values_dir, exist_ok=True)
    with open(os.path.join(values_dir, "ic_launcher_background.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">#0F1015</color>\n</resources>\n')

    print("SUCCESS: Android adaptive icons updated with icon_link.png!")

if __name__ == "__main__":
    generate_icons()
