// Validación del formulario de perfil
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('profile-form');
    const passwordActual = document.getElementById('password_actual');
    const passwordNueva = document.getElementById('password_nueva');
    const passwordConfirmar = document.getElementById('password_confirmar');

    // Validación en tiempo real
    const inputs = form.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        input.addEventListener('blur', () => validateField(input));
        input.addEventListener('input', () => {
            if (input.classList.contains('is-invalid')) {
                validateField(input);
            }
        });
    });

    // Validación de contraseñas
    if (passwordNueva) {
        passwordNueva.addEventListener('input', validatePasswordMatch);
        passwordConfirmar.addEventListener('input', validatePasswordMatch);
    }

    // Validación al enviar
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        
        let isValid = true;
        inputs.forEach(input => {
            if (!validateField(input)) {
                isValid = false;
            }
        });

        // Validar contraseñas si se están cambiando
        if (passwordNueva.value || passwordConfirmar.value || passwordActual.value) {
            if (!validatePasswordChange()) {
                isValid = false;
            }
        }

        if (isValid) {
            form.submit();
        } else {
            showMessage('Por favor, corrige los errores en el formulario', 'error');
            // Scroll al primer error
            const firstError = form.querySelector('.is-invalid');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    });

    // Función de validación individual
    function validateField(field) {
        const value = field.value.trim();
        let isValid = true;
        let errorMsg = '';

        // Limpiar errores previos
        clearFieldError(field);

        // Validar campos requeridos
        if (field.hasAttribute('required') && !value) {
            isValid = false;
            errorMsg = 'Este campo es obligatorio';
        }

        // Validaciones específicas
        if (value) {
            switch (field.type) {
                case 'email':
                    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    if (!emailRegex.test(value)) {
                        isValid = false;
                        errorMsg = 'Ingresa un correo válido';
                    }
                    break;

                case 'tel':
                    const telRegex = /^[0-9]{10}$/;
                    if (!telRegex.test(value.replace(/\s/g, ''))) {
                        isValid = false;
                        errorMsg = 'Ingresa 10 dígitos';
                    }
                    break;

                case 'password':
                    if (field.id === 'password_nueva' && value.length < 8) {
                        isValid = false;
                        errorMsg = 'Mínimo 8 caracteres';
                    }
                    break;
            }

            // Validar código postal
            if (field.id === 'codigo_postal') {
                const cpRegex = /^[0-9]{5}$/;
                if (!cpRegex.test(value)) {
                    isValid = false;
                    errorMsg = 'Ingresa 5 dígitos';
                }
            }

            // Validar RFC
            if (field.id === 'rfc' && value) {
                const rfcRegex = /^[A-ZÑ&]{3,4}[0-9]{6}[A-Z0-9]{3}$/;
                if (!rfcRegex.test(value.toUpperCase())) {
                    isValid = false;
                    errorMsg = 'RFC inválido';
                }
            }
        }

        if (!isValid) {
            showFieldError(field, errorMsg);
        }

        return isValid;
    }

    // Validar que las contraseñas coincidan
    function validatePasswordMatch() {
        if (passwordNueva.value && passwordConfirmar.value) {
            if (passwordNueva.value !== passwordConfirmar.value) {
                showFieldError(passwordConfirmar, 'Las contraseñas no coinciden');
                return false;
            } else {
                clearFieldError(passwordConfirmar);
                return true;
            }
        }
        return true;
    }

    // Validar cambio de contraseña completo
    function validatePasswordChange() {
        const hasNewPassword = passwordNueva.value || passwordConfirmar.value;
        
        if (hasNewPassword && !passwordActual.value) {
            showFieldError(passwordActual, 'Ingresa tu contraseña actual');
            return false;
        }

        if (passwordNueva.value && !passwordConfirmar.value) {
            showFieldError(passwordConfirmar, 'Confirma tu nueva contraseña');
            return false;
        }

        if (passwordNueva.value !== passwordConfirmar.value) {
            showFieldError(passwordConfirmar, 'Las contraseñas no coinciden');
            return false;
        }

        if (passwordNueva.value && passwordNueva.value.length < 8) {
            showFieldError(passwordNueva, 'Mínimo 8 caracteres');
            return false;
        }

        return true;
    }

    // Mostrar error en campo
    function showFieldError(field, message) {
        field.classList.add('is-invalid');
        
        let errorDiv = field.parentElement.querySelector('.error-msg');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'error-msg';
            field.parentElement.appendChild(errorDiv);
        }
        errorDiv.textContent = message;
    }

    // Limpiar error de campo
    function clearFieldError(field) {
        field.classList.remove('is-invalid');
        const errorDiv = field.parentElement.querySelector('.error-msg');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    // Mostrar mensaje general
    function showMessage(message, type = 'success') {
        const messagesContainer = document.querySelector('.messages') || createMessagesContainer();
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;
        
        messagesContainer.appendChild(alert);
        
        // Scroll al mensaje
        alert.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        // Auto-eliminar después de 5 segundos
        setTimeout(() => {
            alert.style.transition = 'opacity 0.3s';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    }

    // Crear contenedor de mensajes si no existe
    function createMessagesContainer() {
        const container = document.createElement('div');
        container.className = 'messages';
        form.parentElement.insertBefore(container, form);
        return container;
    }

    // Formatear RFC automáticamente a mayúsculas
    const rfcInput = document.getElementById('rfc');
    if (rfcInput) {
        rfcInput.addEventListener('input', (e) => {
            e.target.value = e.target.value.toUpperCase();
        });
    }

    // Formatear teléfono solo números
    const telInputs = document.querySelectorAll('input[type="tel"]');
    telInputs.forEach(tel => {
        tel.addEventListener('input', (e) => {
            e.target.value = e.target.value.replace(/\D/g, '').slice(0, 10);
        });
    });

    // Formatear código postal solo números
    const cpInput = document.getElementById('codigo_postal');
    if (cpInput) {
        cpInput.addEventListener('input', (e) => {
            e.target.value = e.target.value.replace(/\D/g, '').slice(0, 5);
        });
    }
});
