import os
import re

# --- CONFIGURACIÓN DE AUDITORÍA ---
EXTENSIONS = ['.json']
SUSPICIOUS_NAMES = ['MasDueños', 'Spazios', 'Tapiola', 'jmt_']

# Regex para detectar números largos que NO sean los ceros que pusimos
# Busca cualquier cadena de 11 dígitos o más que no sea solo ceros
LONG_NUM_REGEX = r'(?<!0)\d{11,}'

def audit_file(file_path):
    findings = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            # 1. Buscar números largos (Posibles IDs reales)
            if re.search(LONG_NUM_REGEX, line):
                findings.append(f"Línea {line_num}: Posible ID real detectado.")

            # 2. Buscar nombres prohibidos
            for name in SUSPICIOUS_NAMES:
                if name.lower() in line.lower():
                    findings.append(f"Línea {line_num}: Nombre sensible '{name}' detectado.")

    return findings

def run_audit():
    print("🔍 Iniciando Auditoría de Seguridad...")
    total_issues = 0

    for root, dirs, files in os.walk('.'):
        if '.git' in root: continue

        for file in files:
            if any(file.endswith(ext) for ext in EXTENSIONS):
                path = os.path.join(root, file)
                issues = audit_file(path)
                if issues:
                    print(f"\n⚠️  {path}:")
                    for issue in issues:
                        print(f"   {issue}")
                    total_issues += len(issues)

    if total_issues == 0:
        print("\n✅ TODO LIMPIO: No se encontraron IDs reales ni nombres sensibles.")
    else:
        print(f"\n❌ AUDITORÍA FALLIDA: Se encontraron {total_issues} posibles filtraciones.")

if __name__ == "__main__":
    run_audit()