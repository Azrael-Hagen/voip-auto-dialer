#!/bin/bash

# Carpeta destino
DEST_DIR="exported_py_txt"

# Crear carpeta si no existe
mkdir -p "$DEST_DIR"

# Buscar todos los archivos .py y copiarlos como .txt
find . -type f -name "*.py" | while read file; do
    # Obtener nombre base del archivo sin extensión
    base=$(basename "$file" .py)
    # Copiar contenido a la carpeta destino con extensión .txt
    cp "$file" "$DEST_DIR/${base}.txt"
done

echo "Todos los archivos .py fueron copiados a $DEST_DIR como .txt"
