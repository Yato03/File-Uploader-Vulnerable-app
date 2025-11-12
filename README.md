# Vulnerable File Uploader
---------------------------------------------------

## Índice
- [Vulnerable File Uploader](#vulnerable-file-uploader)
  - [Índice](#índice)
  - [Credenciales](#credenciales)
  - [Ejecución](#ejecución)
    - [Con docker compose](#con-docker-compose)
    - [Con python](#con-python)
  - [Resumen](#resumen)
  - [Cómo se introdujeron las vulnerabilidades](#cómo-se-introdujeron-las-vulnerabilidades)
  - [Cómo explotarlas (resumen de ataques)](#cómo-explotarlas-resumen-de-ataques)
    - [SQL Injection (login)](#sql-injection-login)
    - [Stored XSS (mensajes)](#stored-xss-mensajes)
    - [Path Traversal (download)](#path-traversal-download)
    - [File upload](#file-upload)

## Credenciales

- `admin:admin123`

## Ejecución

### Con docker compose

1) Tener docker y docker compose instalado.
2) Iniciar: `docker compose up`
3) Acceder a http://localhost:5000

### Con python

1) Tener Python 3.11 instalado.
2) Crear un entorno virtual (recomendado) y activar.

```python
python3 -m venv venv
```

3) Instalar librerías: `pip install -r requirements.txt`
4) Ejecución: `python app.py`
5) Acceder a http://localhost:5000

## Resumen
Se ha implementado una pequeña aplicación web en Flask que contiene **al menos 4 vulnerabilidades reales explotables** para practicar:
1. SQL Injection en login y búsqueda de usuarios.
2. Stored XSS (mensajes) y Reflected XSS (parámetro de búsqueda mostrado sin escapar).
3. Insecure File Handling: subida sin validación y descarga vulnerable a Path Traversal.
4. Insecure Authentication: credenciales por defecto y contraseñas almacenadas en texto plano.

(Ver Enunciado P2 para requisitos). fileciteturn0file0

## Cómo se introdujeron las vulnerabilidades
- SQLi: las consultas SQL se construyen mediante concatenación de strings con parámetros del usuario (sin use de prepared statements). (Tema 5). fileciteturn0file2
- XSS: el contenido publicado por usuarios se almacena y se renderiza usando la bandera `|safe` en Jinja2 (sin escape), lo que permite ejecución de scripts en el navegador. (Tema 6). fileciteturn0file3
- Path Traversal / Insecure File Handling: el parámetro `file` se usa directamente al componer la ruta del fichero descargable, sin canonicalización ni whitelist. (Tema 6). fileciteturn0file3
- Autenticación insegura: contraseña por defecto `admin:admin123` insertada en la BD y contraseñas almacenadas en texto claro. (Tema 5). fileciteturn0file2

## Cómo explotarlas (resumen de ataques)
### SQL Injection (login)
En la página de login se puede inyectar `username` o `password`. Por ejemplo:
`' OR '1'='1' --`
Esto convierte la consulta en verdadera y permite autenticarse como primer usuario (admin).

### Stored XSS (mensajes)
Publicar en el formulario:
`<script>fetch('/download?file=../../../../etc/passwd').then(r=>r.text()).then(t=>alert(t))</script>`
Al abrir la página como otro usuario, el script se ejecutará en su navegador.

### Path Traversal (download)
Pedir:
`/download?file=../../../../etc/passwd`
si el servidor corre en Linux y tiene permisos, podría devolver ficheros arbitrarios.

### File upload
Subir un archivo con extensión .php u otro contenido malicioso; aunque este ejemplo no ejecuta PHP, demuestra falta de validación y posible persistencia de payloads.
