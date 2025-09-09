from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

def generar_factura(cliente, items, total, archivo="factura.pdf"):
    doc = SimpleDocTemplate(archivo, pagesize=letter)
    elementos = []
    estilos = getSampleStyleSheet()

    # Encabezado
    elementos.append(Paragraph(f"Factura para: <b>{cliente['nombre']}</b>", estilos["Title"]))
    elementos.append(Spacer(1, 12))

    # Tabla
    data = [["Producto", "Descripción", "Precio", "Cantidad", "Subtotal"]]
    for item in items:
        data.append([
            item["nombre"],
            item["descripcion"],
            f"${item['precio']:.2f}",
            str(item["cantidad"]),
            f"${item['subtotal']:.2f}"
        ])
    data.append(["", "", "", "TOTAL:", f"${total:.2f}"])

    tabla = Table(data, colWidths=[100, 150, 80, 60, 80])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.gray),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (2, 1), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))
    elementos.append(tabla)

    doc.build(elementos)
    return archivo
