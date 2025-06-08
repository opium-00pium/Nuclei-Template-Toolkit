# convert_icon.py (English Version)
import base64

icon_filename = "design.ico"
output_filename = "icon_data.py"

try:
    with open(icon_filename, "rb") as f:
        b64_data = base64.b64encode(f.read())
    
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(f'icon_base64 = "{b64_data.decode()}"\n')
    
    print(f"Success! Converted '{icon_filename}' to Base64 and saved to '{output_filename}'.")

except FileNotFoundError:
    print(f"Error: Icon file '{icon_filename}' not found.")