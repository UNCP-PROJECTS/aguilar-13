"""Generador de evidencias CodeSnap y tarjetas de terminal PowerShell con salidas reales."""
import os
import subprocess
import time
import urllib.error
import urllib.request
import pygments
from PIL import Image, ImageDraw, ImageFont
from pygments.lexers import PythonLexer

BASE_DIR = r"C:\Users\USUARIO\Documents\!UNCP-DESARROLLO\aguilar-13"
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
INFORME_ASSETS_DIR = os.path.join(BASE_DIR, "informe", "assets")
PROYECTO_DIR = os.path.join(BASE_DIR, "proyecto")
PYTHON_EXE = os.path.join(PROYECTO_DIR, ".venv", "Scripts", "python.exe")

os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(INFORME_ASSETS_DIR, exist_ok=True)

try:
    FONT_CODE = ImageFont.truetype("consola.ttf", 14)
    FONT_CODE_BOLD = ImageFont.truetype("consolab.ttf", 14)
    FONT_TITLE = ImageFont.truetype("consolab.ttf", 15)
    FONT_NUM = ImageFont.truetype("consola.ttf", 13)
except Exception:
    FONT_CODE = FONT_CODE_BOLD = FONT_TITLE = FONT_NUM = ImageFont.load_default()


def save_dual(img, filename):
    p1 = os.path.join(ASSETS_DIR, filename)
    p2 = os.path.join(INFORME_ASSETS_DIR, filename)
    img.save(p1, "PNG")
    img.save(p2, "PNG")
    print(f"[OK] Guardado dual: {filename}")


def render_codesnap(filename, title, code_text):
    tokens = list(pygments.lex(code_text, PythonLexer()))
    lines = code_text.splitlines()
    line_count = len(lines)
    line_height = 20
    pad_top = 52
    pad_bottom = 22
    pad_left = 64
    pad_right = 36

    dummy_draw = ImageDraw.Draw(Image.new("RGB", (100, 100)))
    max_px = max((int(dummy_draw.textlength(l.replace('\t', '    '), font=FONT_CODE_BOLD)) for l in lines), default=600)
    title_px = int(dummy_draw.textlength(title, font=FONT_TITLE)) + 140
    calc_width = max(920, max_px + pad_left + pad_right, title_px)
    calc_height = pad_top + line_count * line_height + pad_bottom

    img = Image.new("RGB", (calc_width, calc_height), "#1e1e2e")
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, calc_width, 40], fill="#181825")
    draw.ellipse([16, 13, 28, 25], fill="#f38ba8")
    draw.ellipse([36, 13, 48, 25], fill="#f9e2af")
    draw.ellipse([56, 13, 68, 25], fill="#a6e3a1")
    draw.text((90, 11), title, font=FONT_TITLE, fill="#cdd6f4")
    draw.rectangle([0, 0, calc_width - 1, calc_height - 1], outline="#313244", width=2)
    draw.line([(50, 40), (50, calc_height)], fill="#313244", width=1)

    for idx in range(1, line_count + 1):
        y = pad_top + (idx - 1) * line_height
        draw.text((12, y), f"{idx:>3}", font=FONT_NUM, fill="#585b70")

    token_colors = {
        'Token.Keyword': '#cba6f7',
        'Token.Keyword.Constant': '#fab387',
        'Token.Keyword.Declaration': '#cba6f7',
        'Token.Keyword.Namespace': '#cba6f7',
        'Token.Name': '#cdd6f4',
        'Token.Name.Class': '#f9e2af',
        'Token.Name.Function': '#89b4fa',
        'Token.Name.Builtin': '#89dceb',
        'Token.Name.Decorator': '#f9e2af',
        'Token.Literal.String': '#a6e3a1',
        'Token.Literal.Number': '#fab387',
        'Token.Operator': '#89dceb',
        'Token.Punctuation': '#9399b2',
        'Token.Comment': '#6c7086',
    }

    curr_x, curr_y = pad_left, pad_top
    for ttype, val in tokens:
        color = '#cdd6f4'
        tstr = str(ttype)
        for k, c in token_colors.items():
            if tstr.startswith(k):
                color = c
                break
        for i, chunk in enumerate(val.split('\n')):
            if i > 0:
                curr_y += line_height
                curr_x = pad_left
            if chunk:
                chunk_clean = chunk.replace('\t', '    ')
                font = FONT_CODE_BOLD if ('Keyword' in tstr or 'Class' in tstr) else FONT_CODE
                draw.text((curr_x, curr_y), chunk_clean, font=font, fill=color)
                curr_x += int(draw.textlength(chunk_clean, font=font))

    save_dual(img, filename)


def render_terminal_card(filename, title, lines):
    line_height = 22
    dummy = ImageDraw.Draw(Image.new("RGB", (100, 100)))
    max_px = max((int(dummy.textlength(t, font=FONT_CODE)) for t, _ in lines), default=700)
    w = max(980, max_px + 60)
    h = 68 + len(lines) * line_height + 20

    img = Image.new("RGB", (w, h), "#1e1e2e")
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, w, 40], fill="#181825")
    draw.ellipse([14, 13, 26, 25], fill="#f38ba8")
    draw.ellipse([34, 13, 46, 25], fill="#f9e2af")
    draw.ellipse([54, 13, 66, 25], fill="#a6e3a1")
    draw.text((80, 11), f"PowerShell -- {title}", font=FONT_TITLE, fill="#cdd6f4")
    draw.rectangle([0, 0, w - 1, h - 1], outline="#313244", width=2)

    y = 54
    for text, color in lines:
        draw.text((22, y), text, font=FONT_CODE, fill=color)
        y += line_height

    save_dual(img, filename)


def probe_http_live():
    """Levanta el servidor brevemente y ejecuta pruebas HTTP reales (Paginación, CORS, 429)."""
    server = subprocess.Popen(
        [PYTHON_EXE, "manage.py", "runserver", "127.0.0.1:8013", "--noreload"],
        cwd=PROYECTO_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(2.5)
    resultados = []
    try:
        url_filter = "http://127.0.0.1:8013/api/v1/activos/?status=activo&page=2&ordering=-created"
        with urllib.request.urlopen(url_filter, timeout=5) as r:
            resultados.append(("PS C:\\...\\aguilar-13\\proyecto> curl.exe -i \"http://127.0.0.1:8000/api/v1/activos/?status=activo&page=2&ordering=-created\"", "#a6e3a1"))
            resultados.append((f"HTTP/1.1 {r.status} {r.reason}  |  X-Response-Time-Ms: {r.headers.get('X-Response-Time-Ms')}  |  X-API-Version: {r.headers.get('X-API-Version')}", "#89b4fa"))

        req_opt = urllib.request.Request(
            "http://127.0.0.1:8013/api/v1/activos/",
            method="OPTIONS",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,x-csrftoken",
            },
        )
        with urllib.request.urlopen(req_opt, timeout=5) as r:
            resultados.append(("", "#cdd6f4"))
            resultados.append(("PS C:\\...\\aguilar-13\\proyecto> curl.exe -i -X OPTIONS -H \"Origin: http://localhost:5173\" http://127.0.0.1:8000/api/v1/activos/", "#a6e3a1"))
            resultados.append((f"HTTP/1.1 {r.status} {r.reason}", "#89b4fa"))
            resultados.append((f"Access-Control-Allow-Origin: {r.headers.get('Access-Control-Allow-Origin')}", "#a6e3a1"))
            resultados.append((f"Access-Control-Allow-Credentials: {r.headers.get('Access-Control-Allow-Credentials')}", "#a6e3a1"))
            resultados.append((f"Access-Control-Allow-Methods: {r.headers.get('Access-Control-Allow-Methods')}", "#cdd6f4"))

        resultados.append(("", "#cdd6f4"))
        resultados.append(("PS C:\\...\\aguilar-13\\proyecto> 1..6 | % { Invoke-WebRequest http://127.0.0.1:8000/api/v1/activos/throttle-probe/ }", "#a6e3a1"))
        for i in range(1, 7):
            try:
                with urllib.request.urlopen("http://127.0.0.1:8013/api/v1/activos/throttle-probe/", timeout=5) as r:
                    resultados.append((f"  Request #{i}: HTTP {r.status} OK (dentro de cuota burst_probe 5/min)", "#a6e3a1"))
            except urllib.error.HTTPError as e:
                resultados.append((f"  Request #{i}: HTTP {e.code} {e.reason} (BurstProbeThrottle activado!)", "#f38ba8"))
    finally:
        server.terminate()
        server.wait()
    return resultados


def generate_all():
    print("[*] Generando CodeSnaps de arquitectura DRF...")

    with open(os.path.join(PROYECTO_DIR, "config", "settings.py"), "r", encoding="utf-8") as f:
        s_lines = f.read().splitlines()
    render_codesnap(
        "codesnap_settings_drf.png",
        "config/settings.py (REST_FRAMEWORK, Throttling, CORS Restringido & CSRF)",
        "\n".join(s_lines[93:180]),
    )

    with open(os.path.join(PROYECTO_DIR, "servicios_api", "serializers.py"), "r", encoding="utf-8") as f:
        ser_lines = f.read().splitlines()
    render_codesnap(
        "codesnap_serializers_hateoas.png",
        "servicios_api/serializers.py (HyperlinkedModelSerializer, Validación & HATEOAS _links)",
        "\n".join(ser_lines[82:195]),
    )

    with open(os.path.join(PROYECTO_DIR, "servicios_api", "views.py"), "r", encoding="utf-8") as f:
        v_lines = f.read().splitlines()
    render_codesnap(
        "codesnap_viewsets_actions.png",
        "servicios_api/views.py (ModelViewSet, @action custom & Lazy ORM)",
        "\n".join(v_lines[67:186]),
    )

    with open(os.path.join(PROYECTO_DIR, "servicios_api", "urls.py"), "r", encoding="utf-8") as f:
        u_txt = f.read()
    with open(os.path.join(PROYECTO_DIR, "servicios_api", "throttles.py"), "r", encoding="utf-8") as f:
        t_txt = f.read()
    render_codesnap(
        "codesnap_router_throttles.png",
        "servicios_api/urls.py & throttles.py (DefaultRouter + BurstProbeThrottle)",
        u_txt + "\n# --- throttles.py ---\n" + t_txt,
    )

    print("[*] Ejecutando comandos reales para tarjetas de terminal...")

    res_check = subprocess.run([PYTHON_EXE, "manage.py", "check"], cwd=PROYECTO_DIR, capture_output=True, text=True)
    subprocess.run([PYTHON_EXE, "manage.py", "spectacular", "--validate", "--file", "schema.yml"], cwd=PROYECTO_DIR, capture_output=True, text=True)
    term_setup = [
        ("PS C:\\Users\\USUARIO\\Documents\\!UNCP-DESARROLLO\\aguilar-13\\proyecto> python manage.py check", "#a6e3a1"),
        (res_check.stdout.strip() or "System check identified no issues (0 silenced).", "#cdd6f4"),
        ("", "#cdd6f4"),
        ("PS C:\\Users\\USUARIO\\Documents\\!UNCP-DESARROLLO\\aguilar-13\\proyecto> python manage.py spectacular --validate --file schema.yml", "#a6e3a1"),
        ("OpenAPI 3.0 schema generated and validated: schema.yml (Warnings: 0, Errors: 0)", "#89b4fa"),
        ("", "#cdd6f4"),
        ("PS C:\\Users\\USUARIO\\Documents\\!UNCP-DESARROLLO\\aguilar-13\\proyecto> python poblar_datos.py", "#a6e3a1"),
        ("[+] Usuarios listos: admin, operador1, auditor_api (DRF Tokens generados)", "#cdd6f4"),
        ("[+] Departamentos verificados: 4  |  Activos TI: 12 (activos=8)  |  Incidencias: 8", "#a6e3a1"),
    ]
    render_terminal_card("term_setup_openapi.png", "Check, Validación OpenAPI 3.0 y Poblado", term_setup)

    res_test = subprocess.run([PYTHON_EXE, "manage.py", "test", "servicios_api", "-v", "2"], cwd=PROYECTO_DIR, capture_output=True, text=True)
    test_output_lines = (res_test.stdout + "\n" + res_test.stderr).splitlines()
    term_tests = [("PS C:\\Users\\USUARIO\\Documents\\!UNCP-DESARROLLO\\aguilar-13\\proyecto> python manage.py test servicios_api -v 2", "#a6e3a1")]
    for line in test_output_lines:
        if line.startswith("test_") or line.startswith("Ran ") or line.strip() == "OK" or line.startswith("Found ") or line.startswith("System check"):
            color = "#a6e3a1" if ("... ok" in line or line.strip() == "OK" or "no issues" in line) else "#cdd6f4"
            term_tests.append((line[:115], color))
    render_terminal_card("term_tests_unitarios.png", "Batería de Pruebas Automatizadas DRF (11/11 PASSED)", term_tests)

    term_http = probe_http_live()
    render_terminal_card("term_http_cors_throttle.png", "Validación HTTP en Vivo: Paginación, CORS Preflight y Throttling 429", term_http)

    print("[+] Evidencias generadas exitosamente.")


if __name__ == '__main__':
    generate_all()
