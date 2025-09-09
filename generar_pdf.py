# generar_pdf.py
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDFS_DIR = os.path.join(BASE_DIR, "pdfs")
os.makedirs(PDFS_DIR, exist_ok=True)

def generar_pdf(productos, nombre_archivo="catalogo.pdf"):
    ruta_pdf = os.path.join(PDFS_DIR, nombre_archivo)
    doc = SimpleDocTemplate(ruta_pdf, pagesize=letter)
    elementos = []
    estilos = getSampleStyleSheet()

    elementos.append(Paragraph("Catálogo de Productos", estilos["Title"]))
    elementos.append(Spacer(1, 12))

    # Table header
    data = [["Imagen", "Producto", "Descripción", "Cantidad", "Precio1", "Precio2", "Subtotal"]]
    total = 0
    for p in productos:
        cantidad = int(p.get("cantidad", 1) or 0)
        precio = float(p.get("precio1", p.get("precio", 0)) or 0)
        subtotal = cantidad * precio
        total += subtotal

        # imagen (si local) -> usar Image de reportlab (tamaño reducido)
        img_path = p.get("imagen_local") or None
        img_obj = ""
        if img_path and os.path.exists(img_path):
            try:
                img_obj = Image(img_path, width=60, height=60)
            except Exception:
                img_obj = ""
        data.append([img_obj, p.get("nombre", ""), p.get("descripcion", ""), str(cantidad), f"${precio:,.2f}", f"${p.get('precio2', '')}", f"${subtotal:,.2f}"])

    data.append(["", "", "", "", "", "Total", f"${total:,.2f}"])

    tabla = Table(data, colWidths=[70, 130, 150, 50, 60, 60, 70])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#4b4b4b")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN", (3,1), (3,-2), "CENTER"),
        ("ALIGN", (4,1), (6,-2), "RIGHT"),
    ]))

    elementos.append(tabla)
    doc.build(elementos)
    return ruta_pdf
