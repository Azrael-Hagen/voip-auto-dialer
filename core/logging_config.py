"""
Sistema de logging centralizado para VoIP Auto Dialer
Configuración unificada con rotación de archivos y múltiples niveles
"""
import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# Configuración global de logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Formato de logs
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configurar sistema de logging centralizado
    
    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Logger principal configurado
    """
    # Crear logger principal
    logger = logging.getLogger("voip_auto_dialer")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Evitar duplicar handlers
    if logger.handlers:
        return logger
    
    # Formatter común
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo principal con rotación
    main_log_file = LOG_DIR / "voip_auto_dialer.log"
    file_handler = logging.handlers.RotatingFileHandler(
        main_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler para errores críticos
    error_log_file = LOG_DIR / "errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    logger.info("Sistema de logging inicializado")
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Obtener logger específico para un módulo
    
    Args:
        name: Nombre del módulo/componente
        
    Returns:
        Logger configurado para el módulo
    """
    # Asegurar que el logging principal esté configurado
    main_logger = logging.getLogger("voip_auto_dialer")
    if not main_logger.handlers:
        setup_logging()
    
    # Crear logger específico
    module_logger = logging.getLogger(name)
    
    # Si ya tiene handlers, devolverlo
    if module_logger.handlers:
        return module_logger
    
    # Configurar logger del módulo
    module_logger.setLevel(logging.DEBUG)
    
    # Formatter
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # Handler para archivo específico del módulo
    module_log_file = LOG_DIR / f"{name.replace('.', '_')}.log"
    module_handler = logging.handlers.RotatingFileHandler(
        module_log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=2,
        encoding='utf-8'
    )
    module_handler.setLevel(logging.DEBUG)
    module_handler.setFormatter(formatter)
    module_logger.addHandler(module_handler)
    
    # También enviar al logger principal
    module_logger.parent = main_logger
    
    return module_logger

def log_system_event(event_type: str, message: str, level: str = "INFO"):
    """
    Registrar evento del sistema
    
    Args:
        event_type: Tipo de evento (startup, shutdown, error, etc.)
        message: Mensaje del evento
        level: Nivel de logging
    """
    logger = get_logger("system_events")
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(f"[{event_type.upper()}] {message}")

def log_call_event(call_id: str, event: str, details: Dict = None):
    """
    Registrar evento de llamada
    
    Args:
        call_id: ID de la llamada
        event: Tipo de evento (initiated, answered, completed, etc.)
        details: Detalles adicionales del evento
    """
    logger = get_logger("call_events")
    details_str = f" - {details}" if details else ""
    logger.info(f"Call {call_id}: {event.upper()}{details_str}")

def log_agent_event(agent_id: str, event: str, details: Dict = None):
    """
    Registrar evento de agente
    
    Args:
        agent_id: ID del agente
        event: Tipo de evento (login, logout, status_change, etc.)
        details: Detalles adicionales del evento
    """
    logger = get_logger("agent_events")
    details_str = f" - {details}" if details else ""
    logger.info(f"Agent {agent_id}: {event.upper()}{details_str}")

# Configurar logging al importar el módulo
setup_logging()