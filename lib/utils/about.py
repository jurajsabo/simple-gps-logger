from kivy.metrics import sp
from kivymd.icon_definitions import md_icons

from config import app_name, app_version, year, author


# About text
size1 = int(sp(18))
size2 = int(sp(16))


about_text = \
f''' 
    [size={size1}][b]{app_name}[/b][/size]
    version {app_version}

    [i]Ensure the app is not Battery optimized and not Background restricted in Android settings.[/i]

    A simple GPS tracking app that records your location coordinates and exports them as GPX or CSV files.

    [size={size2}][b]Features[/b][/size]

    [b]• Easy Tracking[/b] - One-tap start/pause/stop GPS logging
    [b]• Dual Export[/b] - Save as GPX (mapping or GIS software) or CSV (data analysis)
    [b]• Privacy First[/b] - All data stays on your device, no cloud uploads

    [size={size2}][b]Copyright[/b][/size]

    [font=Icons]{md_icons["copyright"]}[/font] {year} {author}.
    All rights reserved.
    Licensed under GPL v3.0.

    [i][font=Icons]{md_icons["web"]}[/font] [ref=web][color=0066cc][u]Website[/u][/color][/ref][/i]
    [i][font=Icons]{md_icons["shield"]}[/font] [ref=privacy][color=0066cc][u]Privacy Policy[/u][/color][/ref][/i]
    [i][font=Icons]{md_icons["file-document"]}[/font] [ref=license][color=0066cc][u]License[/u][/color][/ref][/i]
    [i][font=Icons]{md_icons["code-tags"]}[/font] [ref=code][color=0066cc][u]Source Code[/u][/color][/ref][/i]

    [i]Caution: The Enemy Is Listening.[/i]

'''.replace(' ' * 4, '')
