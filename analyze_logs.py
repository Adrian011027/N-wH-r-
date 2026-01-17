#!/usr/bin/env python3
"""
Script para analizar y filtrar logs de pagos de Conekta
Uso:
    python analyze_logs.py                 # Mostrar resumen
    python analyze_logs.py --errors        # Solo errores
    python analyze_logs.py --last 100      # Últimas 100 líneas
    python analyze_logs.py --search "token"  # Buscar palabra clave
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Colores para terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def find_log_files():
    """Encuentra archivos de log de Conekta"""
    base_dir = Path(__file__).parent
    logs_dir = base_dir / 'logs'
    
    if not logs_dir.exists():
        print(f"{Colors.RED}❌ Carpeta de logs no encontrada: {logs_dir}{Colors.ENDC}")
        return None
    
    log_files = {
        'conekta': logs_dir / 'conekta_payments.log',
        'debug': logs_dir / 'payments_debug.log',
        'errors': logs_dir / 'payment_errors.log'
    }
    
    return log_files

def read_log_file(file_path, last_n=None):
    """Lee un archivo de log"""
    if not file_path.exists():
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        if last_n:
            return lines[-last_n:]
        return lines
    except Exception as e:
        print(f"{Colors.RED}Error leyendo {file_path}: {e}{Colors.ENDC}")
        return []

def extract_payment_sessions(lines):
    """Extrae sesiones de pago de los logs"""
    sessions = []
    current_session = None
    
    for line in lines:
        if '[PROCESAR_PAGO_CONEKTA]' in line and 'INICIANDO' in line:
            if current_session:
                sessions.append(current_session)
            current_session = {'lines': [line], 'timestamp': line[:19]}
        elif current_session:
            current_session['lines'].append(line)
            
            if 'Status HTTP:' in line:
                status_part = line.split('Status HTTP:')[-1].strip()
                current_session['http_status'] = status_part[:3]
            
            if 'Error' in line or 'ERROR' in line:
                current_session['has_error'] = True
            
            if '✅ PAGO PROCESADO EXITOSAMENTE' in line:
                current_session['success'] = True
    
    if current_session:
        sessions.append(current_session)
    
    return sessions

def print_summary(log_files):
    """Imprime resumen de los logs"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}📊 RESUMEN DE LOGS DE CONEKTA{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.ENDC}\n")
    
    for name, path in log_files.items():
        if path.exists():
            file_size = path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            mod_time = datetime.fromtimestamp(path.stat().st_mtime)
            
            color = Colors.GREEN if name != 'errors' else Colors.RED
            print(f"{color}📄 {name.upper():15} {Colors.ENDC}")
            print(f"   Path: {path}")
            print(f"   Size: {file_size_mb:.2f} MB")
            print(f"   Last modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
        else:
            print(f"{Colors.YELLOW}⚠️  {name.upper():15} - No existe (aún){Colors.ENDC}\n")

def print_errors(log_files):
    """Muestra los errores"""
    print(f"\n{Colors.BOLD}{Colors.RED}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.RED}❌ ERRORES Y ADVERTENCIAS{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.RED}{'='*80}{Colors.ENDC}\n")
    
    error_lines = read_log_file(log_files['errors'])
    
    if not error_lines:
        print(f"{Colors.GREEN}✅ No hay errores registrados{Colors.ENDC}\n")
        return
    
    for line in error_lines:
        if 'ERROR' in line:
            print(f"{Colors.RED}{line.rstrip()}{Colors.ENDC}")
        elif 'WARNING' in line:
            print(f"{Colors.YELLOW}{line.rstrip()}{Colors.ENDC}")
        else:
            print(line.rstrip())

def print_last_payments(log_files, n=5):
    """Muestra los últimos pagos procesados"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}💳 ÚLTIMOS {n} PAGOS PROCESADOS{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.ENDC}\n")
    
    lines = read_log_file(log_files['conekta'])
    sessions = extract_payment_sessions(lines)
    
    if not sessions:
        print(f"{Colors.YELLOW}⚠️  No hay sesiones de pago registradas{Colors.ENDC}\n")
        return
    
    for session in sessions[-n:]:
        timestamp = session.get('timestamp', 'Unknown')
        http_status = session.get('http_status', '???')
        has_error = session.get('has_error', False)
        success = session.get('success', False)
        
        status_color = Colors.GREEN if success else (Colors.RED if has_error else Colors.YELLOW)
        status_icon = '✅' if success else ('❌' if has_error else '⏳')
        
        print(f"{status_color}{status_icon} {timestamp} | HTTP: {http_status}{Colors.ENDC}")
        
        # Buscar carrito_id y monto
        for line in session['lines']:
            if 'carrito_id:' in line:
                print(f"   Carrito: {line.split('carrito_id:')[-1].split()[0]}")
            if 'Total calculado:' in line:
                monto = line.split('Total calculado:')[-1].strip()
                print(f"   Monto: {monto}")
        print()

def print_stats(log_files):
    """Imprime estadísticas"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}📈 ESTADÍSTICAS{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.ENDC}\n")
    
    lines = read_log_file(log_files['conekta'])
    sessions = extract_payment_sessions(lines)
    
    total = len(sessions)
    successful = len([s for s in sessions if s.get('success')])
    errors = len([s for s in sessions if s.get('has_error')])
    pending = total - successful - errors
    
    if total == 0:
        print(f"{Colors.YELLOW}⚠️  Sin datos de pagos{Colors.ENDC}\n")
        return
    
    print(f"Total de intentos:    {Colors.BOLD}{total}{Colors.ENDC}")
    print(f"  {Colors.GREEN}✅ Exitosos:      {successful}{Colors.ENDC} ({successful/total*100:.1f}%)")
    print(f"  {Colors.RED}❌ Con errores:   {errors}{Colors.ENDC} ({errors/total*100:.1f}%)")
    print(f"  {Colors.YELLOW}⏳ Pendientes:     {pending}{Colors.ENDC} ({pending/total*100:.1f}%)")
    print()

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Analizar logs de pagos de Conekta',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python analyze_logs.py                # Mostrar resumen
  python analyze_logs.py --errors       # Solo errores
  python analyze_logs.py --last 50      # Últimas 50 líneas
  python analyze_logs.py --search "token"  # Buscar palabra
  python analyze_logs.py --stats        # Estadísticas
        """
    )
    
    parser.add_argument('--errors', action='store_true', help='Mostrar solo errores')
    parser.add_argument('--last', type=int, help='Últimas N líneas de conekta_payments.log')
    parser.add_argument('--search', type=str, help='Buscar palabra clave')
    parser.add_argument('--stats', action='store_true', help='Mostrar estadísticas')
    
    args = parser.parse_args()
    
    log_files = find_log_files()
    if not log_files:
        sys.exit(1)
    
    if args.errors:
        print_errors(log_files)
    elif args.last:
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}📄 ÚLTIMAS {args.last} LÍNEAS{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.ENDC}\n")
        lines = read_log_file(log_files['conekta'], args.last)
        for line in lines:
            print(line.rstrip())
    elif args.search:
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}🔍 BÚSQUEDA: '{args.search}'{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.ENDC}\n")
        lines = read_log_file(log_files['conekta'])
        results = [l for l in lines if args.search.lower() in l.lower()]
        if results:
            for line in results:
                print(line.rstrip())
        else:
            print(f"{Colors.YELLOW}No se encontraron resultados{Colors.ENDC}\n")
    elif args.stats:
        print_summary(log_files)
        print_stats(log_files)
        print_last_payments(log_files, n=3)
    else:
        # Resumen por defecto
        print_summary(log_files)
        print_stats(log_files)
        print_last_payments(log_files, n=3)
        print(f"{Colors.CYAN}💡 Tip: Ejecuta 'python analyze_logs.py --errors' para ver errores{Colors.ENDC}\n")

if __name__ == '__main__':
    main()
