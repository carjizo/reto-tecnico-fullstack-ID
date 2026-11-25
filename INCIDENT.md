# Incidente: pedidos que se quedaban esperando

**Qué pasó:** varias peticiones a la orden se quedaron esperando hasta que el sistema las cortó con error 504 (tiempo agotado).

**Causa probable:** el servicio no pudo leer la contraseña de la base de datos. Entonces cada conexión se quedaba esperando, y las conexiones disponibles se llenaron. Las peticiones nuevas tardaron más de 29 segundos, que es el límite del ApiGateway (tiempo de espera).

**Qué hacer inmediatamente:**
1. Devolver el valor del permiso para leer la contraseña.
2. Si el problema empezó con un cambio reciente, deshacer ese cambio.
3. Reiniciar el servicio para liberar las conexiones atascadas.

**Cómo evitar que vuelva a pasar:**
- Avisos automáticos cuando el servicio no pueda leer la contraseña o cuando las peticiones tarden mucho.
- Revisar los cambios de permisos antes de subirlos.
- Hacer que el servicio responda con error en pocos segundos, sin esperar hasta el límite de 29 (a nivel de código).
