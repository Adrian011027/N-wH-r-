"""
Utilidad centralizada para normalización de género.
Única fuente de verdad para mapear parámetros de URL/API a valores de BD.

Valores en BD: 'Hombre', 'Mujer', 'Unisex'
"""

# Mapeo canónico: parámetro (lowercase) → valor de BD
GENERO_MAP = {
    'hombre': 'Hombre',
    'mujer': 'Mujer',
    'unisex': 'Unisex',
    'dama': 'Mujer',
    'caballero': 'Hombre',
    'h': 'Hombre',
    'm': 'Mujer',
    'u': 'Unisex',
    'todo': 'Todo',      # Todas las colecciones sin filtro de género
    'todos': 'Todo',
}

# Mapeo de sección URL → código de género en BD
SECCION_MAP = {
    'dama': 'Mujer',
    'mujer': 'Mujer',
    'caballero': 'Hombre',
    'hombre': 'Hombre',
}

# Géneros a incluir en filtros (incluye Unisex)
GENERO_FILTER_MAP = {
    'hombre': ['Hombre', 'Unisex'],
    'mujer': ['Mujer', 'Unisex'],
    'unisex': ['Unisex'],
    'dama': ['Mujer', 'Unisex'],
    'caballero': ['Hombre', 'Unisex'],
    'h': ['Hombre', 'Unisex'],
    'm': ['Mujer', 'Unisex'],
    'u': ['Unisex'],
}


def normalize_genero(param):
    """
    Normaliza un parámetro de género a su valor en BD.
    Retorna None si no se reconoce.
    
    >>> normalize_genero('dama')
    'Mujer'
    >>> normalize_genero('HOMBRE')
    'Hombre'
    >>> normalize_genero('xyz')
    None
    """
    if not param:
        return None
    return GENERO_MAP.get(param.lower().strip())


def get_genero_filter(param):
    """
    Retorna lista de géneros para filtrar en BD (incluye Unisex).
    Retorna lista vacía si no se reconoce.
    
    >>> get_genero_filter('hombre')
    ['Hombre', 'Unisex']
    """
    if not param:
        return []
    return GENERO_FILTER_MAP.get(param.lower().strip(), [])


def get_seccion(genero_cod):
    """
    Retorna el nombre de sección para templates ('dama' o 'caballero').
    
    >>> get_seccion('Mujer')
    'dama'
    >>> get_seccion('Hombre')
    'caballero'
    """
    return 'dama' if genero_cod == 'Mujer' else 'caballero'
