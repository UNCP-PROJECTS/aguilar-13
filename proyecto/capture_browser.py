"""Captura de interfaces reales (Consola SPA/HATEOAS, DRF Browsable, Swagger, ReDoc y Health)."""
import os
import shutil
import subprocess
import time
from playwright.sync_api import sync_playwright

BASE_DIR = r"C:\Users\USUARIO\Documents\!UNCP-DESARROLLO\aguilar-13"
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
INFORME_ASSETS_DIR = os.path.join(BASE_DIR, "informe", "assets")
PROYECTO_DIR = os.path.join(BASE_DIR, "proyecto")
PYTHON_EXE = os.path.join(PROYECTO_DIR, ".venv", "Scripts", "python.exe")
CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(INFORME_ASSETS_DIR, exist_ok=True)


def save_dual(src_path, filename):
    shutil.copy(src_path, os.path.join(ASSETS_DIR, filename))
    shutil.copy(src_path, os.path.join(INFORME_ASSETS_DIR, filename))
    print(f"[OK] Captura web guardada: {filename}")


def capture():
    print("[*] Iniciando servidor Django temporal en 127.0.0.1:8014 para capturas Playwright...")
    server_process = subprocess.Popen(
        [PYTHON_EXE, "manage.py", "runserver", "127.0.0.1:8014", "--noreload"],
        cwd=PROYECTO_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(2.5)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=CHROME_EXE, headless=True)
            context = browser.new_context(viewport={'width': 1340, 'height': 860}, device_scale_factor=1.5)
            page = context.new_page()

            def snap(filename, full=False):
                tmp = os.path.join(ASSETS_DIR, f"_tmp_{filename}")
                page.screenshot(path=tmp, full_page=full)
                save_dual(tmp, filename)
                if os.path.exists(tmp):
                    os.remove(tmp)

            # 1. Consola SPA/AJAX inicial con filtros ?status=activo&page=1&ordering=-created y HATEOAS
            page.goto("http://127.0.0.1:8014/")
            page.wait_for_load_state("networkidle")
            time.sleep(1.2)
            snap("interfaz_consola_spa.png", full=True)

            # 2. Autenticación SPA (X-CSRFToken) + Página 2 (?status=activo&page=2&ordering=-created)
            page.click("#btnSpaLogin")
            time.sleep(0.9)
            page.click("#btnNextPage")
            time.sleep(1.0)
            snap("interfaz_paginacion_hateoas.png", full=True)

            # 3. Validación cruzada HTTP 400 (CRITICA con SLA=36h > 12h) desde SPA con X-CSRFToken
            page.fill("#nuevoNombre", "Microservicio Validación SLA")
            page.select_option("#nuevaCriticidad", "CRITICA")
            page.fill("#nuevoSla", "36")
            page.click("#btnCrearActivo")
            time.sleep(1.0)
            snap("interfaz_validacion_400.png", full=True)

            # 4. Prueba en vivo de Throttling 429 Too Many Requests
            page.click("button:has-text('Probar Throttling')")
            time.sleep(1.4)
            snap("interfaz_throttling_429.png", full=True)

            # 5. DRF Browsable API nativa con HATEOAS y Paginación (?status=activo&page=2&ordering=-created)
            page.goto("http://127.0.0.1:8014/api/v1/activos/?status=activo&page=2&ordering=-created")
            page.wait_for_load_state("networkidle")
            time.sleep(0.8)
            snap("interfaz_drf_browsable.png")

            # 6. Swagger UI (/api/docs/) generado con drf-spectacular
            page.goto("http://127.0.0.1:8014/api/docs/")
            page.wait_for_load_state("networkidle")
            time.sleep(2.0)
            snap("interfaz_swagger_ui.png")

            # 7. ReDoc OpenAPI (/api/redoc/)
            page.goto("http://127.0.0.1:8014/api/redoc/")
            page.wait_for_load_state("networkidle")
            time.sleep(2.5)
            snap("interfaz_redoc_ui.png")

            # 8. Health Check Microservicios (/api/v1/health/) en DRF Browsable
            page.goto("http://127.0.0.1:8014/api/v1/health/")
            page.wait_for_load_state("networkidle")
            time.sleep(0.8)
            snap("interfaz_health_microservicio.png")

            # 9. Consola Django Admin de Activos TI (ya autenticados como admin en sesión SPA)
            page.goto("http://127.0.0.1:8014/admin/servicios_api/activoti/")
            page.wait_for_load_state("networkidle")
            time.sleep(0.8)
            snap("interfaz_django_admin.png")

            browser.close()
            print("[+] Todas las capturas web generadas exitosamente.")
    finally:
        server_process.terminate()
        server_process.wait()
        print("[*] Servidor temporal detenido.")


if __name__ == '__main__':
    capture()
