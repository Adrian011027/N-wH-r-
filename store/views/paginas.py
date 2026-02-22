"""
Vistas de páginas estáticas / legales.
Aviso de Privacidad, Términos, Política de Cambios, FAQ, Sobre Nosotros,
Guía de Tallas, Métodos de Pago.
"""
from django.shortcuts import render


def aviso_privacidad(request):
    return render(request, "public/legal/aviso-privacidad.html")

def terminos_condiciones(request):
    return render(request, "public/legal/terminos-condiciones.html")

def politica_cambios(request):
    return render(request, "public/legal/politica-cambios.html")

def preguntas_frecuentes(request):
    return render(request, "public/legal/preguntas-frecuentes.html")

def sobre_nosotros(request):
    return render(request, "public/legal/sobre-nosotros.html")

def guia_tallas(request):
    return render(request, "public/legal/guia-tallas.html")

def metodos_pago(request):
    return render(request, "public/legal/metodos-pago.html")
