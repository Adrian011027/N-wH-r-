from django.shortcuts import render
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Q
from store.models import Cliente
from store.utils.security import password_reset_limiter, rate_limit
import threading
import logging

logger = logging.getLogger(__name__)


# ───────────────────────────────────────────────
# API: Solicitar reset (AJAX desde panel cascada)
# ───────────────────────────────────────────────
@csrf_exempt
@require_POST
@rate_limit(password_reset_limiter)
def solicitar_reset_api(request):
    import json
    try:
        body = json.loads(request.body)
        email = (body.get("email") or "").strip().lower()
    except (json.JSONDecodeError, AttributeError):
        email = (request.POST.get("email") or "").strip().lower()

    if not email:
        return JsonResponse({"ok": False, "error": "Introduce un correo electrónico."}, status=400)

    # Buscar por username o correo (case-insensitive)
    cliente = Cliente.objects.filter(
        Q(username__iexact=email) | Q(correo__iexact=email)
    ).first()

    # Siempre retornar éxito para prevenir enumeración de emails
    if not cliente:
        return JsonResponse({"ok": True})

    uidb64 = urlsafe_base64_encode(force_bytes(cliente.pk))
    token  = default_token_generator.make_token(cliente)
    link   = request.build_absolute_uri(
        reverse("cliente_reset_password_confirm",
                kwargs={"uidb64": uidb64, "token": token})
    )

    context = {"nombre": getattr(cliente, "nombre", "Cliente"), "link": link}
    text_body = render_to_string("public/emails/reset_password_email.txt", context)
    html_body = render_to_string("public/emails/reset_password_email.html", context)

    email_msg = EmailMultiAlternatives(
        subject="Recuperación de contraseña – NöwHėrē",
        body=text_body,
        from_email=f"NöwHėrē <{settings.DEFAULT_FROM_EMAIL}>",
        to=[email],
    )
    email_msg.attach_alternative(html_body, "text/html")
    enviar_correo_async(email_msg)

    return JsonResponse({"ok": True})


# ───────────────────────────────────────────────
# Solicitar reset
# ───────────────────────────────────────────────
def solicitar_reset(request):
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()

        # Buscar por username o correo (case-insensitive)
        cliente = Cliente.objects.filter(
            Q(username__iexact=email) | Q(correo__iexact=email)
        ).first()

        # Siempre mostrar confirmación para prevenir enumeración
        if not cliente:
            return render(request, "public/password/confirmacion-envio-correo.html")

        uidb64 = urlsafe_base64_encode(force_bytes(cliente.pk))
        token  = default_token_generator.make_token(cliente)
        link   = request.build_absolute_uri(
            reverse("cliente_reset_password_confirm",
                    kwargs={"uidb64": uidb64, "token": token})
        )

        context = {"nombre": getattr(cliente, "nombre", "Cliente"), "link": link}

        text_body = render_to_string("public/emails/reset_password_email.txt", context)
        html_body = render_to_string("public/emails/reset_password_email.html", context)

        email_msg = EmailMultiAlternatives(
            subject="Recuperación de contraseña – NöwHėrē",
            body=text_body,
            from_email=f"NöwHėrē <{settings.DEFAULT_FROM_EMAIL}>",
            to=[email],
        )
        email_msg.attach_alternative(html_body, "text/html")
        enviar_correo_async(email_msg)

        return render(request, "public/password/confirmacion-envio-correo.html")

    return render(request, "public/password/recuperar-password.html")


# ───────────────────────────────────────────────
# Confirmar enlace
# ───────────────────────────────────────────────
def reset_password_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        cliente = Cliente.objects.get(pk=uid)
    except (Cliente.DoesNotExist, ValueError, TypeError, OverflowError):
        cliente = None

    if cliente and default_token_generator.check_token(cliente, token):
        return render(request, "public/password/recuperar-nuevo-password.html", {
            "uidb64": uidb64,
            "token": token,
        })
    else:
        return render(request, "public/password/recuperar-invalid-token.html")


# ───────────────────────────────────────────────
# Guardar nueva contraseña
# ───────────────────────────────────────────────
def reset_password_submit(request, uidb64, token):
    if request.method == "POST":
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            cliente = Cliente.objects.get(pk=uid)
        except (Cliente.DoesNotExist, ValueError, TypeError, OverflowError):
            cliente = None

        if cliente and default_token_generator.check_token(cliente, token):
            pass1 = request.POST.get("password1")
            pass2 = request.POST.get("password2")

            if not pass1 or not pass2:
                return render(request,
                              "public/password/recuperar-nuevo-password.html",
                              {"uidb64": uidb64, "token": token,
                               "error": "Debes escribir la contraseña dos veces."})

            if pass1 != pass2:
                return render(request,
                              "public/password/recuperar-nuevo-password.html",
                              {"uidb64": uidb64, "token": token,
                               "error": "Las contraseñas no coinciden."})

            # Validar complejidad de contraseña
            try:
                validate_password(pass1, cliente)
            except ValidationError as e:
                return render(request,
                              "public/password/recuperar-nuevo-password.html",
                              {"uidb64": uidb64, "token": token,
                               "error": e.messages[0]})

            cliente.set_password(pass1)
            cliente.save()
            return render(request, "public/password/recuperar-exito.html")

    return render(request, "public/password/recuperar-invalid-token.html")


# ───────────────────────────────────────────────
# Helper: enviar correo en segundo plano
# ───────────────────────────────────────────────
def enviar_correo_async(email_msg):
    threading.Thread(target=email_msg.send, kwargs={"fail_silently": False}).start()
