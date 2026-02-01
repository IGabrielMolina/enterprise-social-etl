import os
import re

# --- CONFIGURACIÓN ---
# Extensiones a procesar
EXTENSIONS = ['.json']
# Reemplazo por defecto
REDACTED = "0000000000"

# Patrones de búsqueda (Regex)
PATTERNS = [
    # 1. Busca "id": "letrasYNumeros" (IDs de credenciales n8n)
    (r'"id":\s*"[a-zA-Z0-9]{15,20}"', f'"id": "{REDACTED}"'),
    # 2. Busca "playlistId": "cualquierCosa"
    (r'"playlistId":\s*"[^"]+"', f'"playlistId": "{REDACTED}"'),
    # 3. Busca IDs numéricos largos (Meta Page IDs, User IDs de +10 dígitos)
    (r'":\s*"\d{10,}"', f'": "{REDACTED}"'),
    # 4. Busca el ID de playlist específico que tenías en el código JS
    (r'playList:"[a-zA-Z0-9_-]+"', f'playList:"{REDACTED}"')
]

def clean_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    for pattern, replacement in PATTERNS:
        content = re.sub(pattern, replacement, content)

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Anonimizado: {file_path}")

def run():
    print("🚀 Iniciando limpieza de datos privados...")
    for root, dirs, files in os.walk('.'):
        # Evitar carpetas ocultas de git
        if '.git' in root:
            continue

        for file in files:
            if any(file.endswith(ext) for ext in EXTENSIONS):
                if file == 'anonymize_etl.py': continue
                clean_file(os.path.join(root, file))
    print("✨ Proceso terminado. Tus JSON están limpios.")

if __name__ == "__main__":
    run()