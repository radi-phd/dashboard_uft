from playwright.sync_api import sync_playwright
import time
import subprocess
import webbrowser

# ============================================================
# INICIA STREAMLIT
# ============================================================

print("Iniciando dashboard...")

processo = subprocess.Popen(
    [
        "py",
        "-m",
        "streamlit",
        "run",
        "dashboard.py"
    ]
)

# ============================================================
# AGUARDA O DASHBOARD
# ============================================================

time.sleep(15)

url = "http://localhost:8501"

print("Abrindo dashboard...")

webbrowser.open(url)

# ============================================================
# GERA PDF E IMAGEM
# ============================================================

with sync_playwright() as p:

    browser = p.chromium.launch()

    page = browser.new_page(
        viewport={
            "width": 1600,
            "height": 5000
        }
    )

    page.goto(url)

    # espera carregar os gráficos
    time.sleep(20)

    # ========================================================
    # PDF
    # ========================================================

    page.pdf(
        path="Dashboard_Institucional.pdf",
        format="A4",
        print_background=True
    )

    # ========================================================
    # IMAGEM
    # ========================================================

    page.screenshot(
        path="Dashboard_Institucional.png",
        full_page=True
    )

    browser.close()

# ============================================================
# FINALIZA
# ============================================================

processo.terminate()

print("\nPDF GERADO COM SUCESSO!")
print("Arquivo: Dashboard_Institucional.pdf")

print("\nIMAGEM GERADA COM SUCESSO!")
print("Arquivo: Dashboard_Institucional.png")