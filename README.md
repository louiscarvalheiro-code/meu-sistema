# Meu Sistema (Flask) - Versão completa com PDF export

Conteúdo:
- app.py - aplicação Flask
- templates/ - templates Jinja2
- static/styles.css - CSS simples
- requirements.txt - dependências
- Procfile / render.yaml - deploy no Render.com

**PDF server-side**: a rota `/relatorio/pdf` usa `pdfkit` que depende do binário `wkhtmltopdf` estar disponível no ambiente.
No Render ou no servidor, instala o `wkhtmltopdf` (ou use um buildpack que o inclua).

### Como correr localmente (exemplo):
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# opcional: instalar wkhtmltopdf no sistema
python app.py
```

### Notas
- Se `wkhtmltopdf` não estiver instalado, a geração de PDF vai falhar e o utilizador recebe uma mensagem. A impressão pelo browser (`window.print()`) funciona sem dependências extras.
