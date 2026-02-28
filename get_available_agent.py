#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def get_available_agent():
    try:
        extensions_file = Path("/home/azrael/voip-auto-dialer/data/extensions.json")
        if not extensions_file.exists():
            return ""
        
        with open(extensions_file, 'r') as f:
            extensions = json.load(f)
        
        # Buscar primera extensión asignada
        for ext_num, ext_data in extensions.items():
            if ext_data.get('assigned', False):
                return ext_num
        
        # Si no hay asignadas, usar la primera disponible
        return list(extensions.keys())[0] if extensions else ""
    
    except Exception:
        return ""

if __name__ == "__main__":
    print(get_available_agent())
