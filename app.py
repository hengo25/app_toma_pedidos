import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import firebase_utils as fu


app = Flask(__name__)
app.secret_key = "dev-secret"

STATIC_DIR = os.path.join(os.getcwd(), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

PER_PAGE = 8  # productos por página en crear_pedido


# ---------------- PDF helper ----------------
def generar_pdf(path, cliente, items, total):
    doc = SimpleDocTemplate(path, pagesize=letter)
    styles = getSampleStyleSheet()
    elems = []

    elems.append(Paragraph("Factura / Pedido", styles["Title"]))
    elems.append(Spacer(1, 8))
    elems.append(Paragraph(f"Cliente: {cliente.get('nombre','')}", styles["Normal"]))
    if cliente.get("direccion"):
        elems.append(Paragraph(f"Dirección: {cliente.get('direccion')}", styles["Normal"]))
    elems.append(Spacer(1, 12))

    estilo_celda = ParagraphStyle(
        name="celda",
        fontSize=9,
        leading=11,
        wordWrap="CJK"  # permite saltos de línea en celdas largas
    )

    data = [["Producto", "Laboratorio", "Cantidad", "Precio", "Subtotal"]]
    for it in items:
        data.append([
            Paragraph(it["nombre"], estilo_celda),
            Paragraph(it.get("laboratorio", ""), estilo_celda),
            str(it["cantidad"]),
            f"${it['precio']:.2f}",
            f"${it['subtotal']:.2f}"
        ])
    data.append(["", "", "", "TOTAL", f"${total:.2f}"])

    table = Table(data, colWidths=[200, 120, 60, 80, 80])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (2, 1), (2, -2), "CENTER"),
        ("ALIGN", (3, 1), (4, -2), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elems.append(table)
    doc.build(elems)


# ---------------- Routes ----------------
@app.route("/")
def index():
    return render_template("index.html")


# (Clientes y productos: sin cambios - los dejo tal como los tienes)
@app.route("/clientes")
def clientes():
    page = request.args.get("page", 1, type=int)
    per_page = 10
    data = fu.get_all("clientes")
    total = len(data)
    pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    return render_template("clientes.html", clientes=data[start:end], page=page, pages=pages)


@app.route("/clientes/nuevo", methods=["POST"])
def clientes_nuevo():
    nombre = request.form.get("nombre", "").strip()
    direccion = request.form.get("direccion", "").strip()
    if not nombre:
        flash("Nombre requerido", "danger")
        return redirect(url_for("clientes"))
    fu.add("clientes", {"nombre": nombre, "direccion": direccion})
    flash("Cliente agregado", "success")
    return redirect(url_for("clientes"))


@app.route("/clientes/editar/<id>", methods=["GET", "POST"])
def clientes_editar(id):
    if request.method == "GET":
        c = fu.get_doc("clientes", id)
        if not c:
            flash("Cliente no encontrado", "warning")
            return redirect(url_for("clientes"))
        return render_template("editar_cliente.html", cliente=c)

    nombre = request.form.get("nombre", "").strip()
    direccion = request.form.get("direccion", "").strip()
    fu.update("clientes", id, {"nombre": nombre, "direccion": direccion})
    flash("Cliente actualizado", "success")
    return redirect(url_for("clientes"))


@app.route("/clientes/eliminar/<id>")
def clientes_eliminar(id):
    fu.delete("clientes", id)
    flash("Cliente eliminado", "warning")
    return redirect(url_for("clientes"))


# ---------------- Productos ----------------
@app.route("/productos")
def productos():
    page = request.args.get("page", 1, type=int)
    per_page = 10
    data = fu.get_all("productos")
    total = len(data)
    pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    return render_template("productos.html", productos=data[start:end], page=page, pages=pages)


@app.route("/productos/nuevo", methods=["POST"])
def productos_nuevo():
    nombre = request.form.get("nombre", "").strip()
    laboratorio = request.form.get("laboratorio", "").strip()
    try:
        precio = float(request.form.get("precio", "0"))
        stock = int(request.form.get("stock", "0"))
    except:
        flash("Precio o stock inválido", "danger")
        return redirect(url_for("productos"))
    fu.add("productos", {"nombre": nombre, "laboratorio": laboratorio, "precio": precio, "stock": stock})
    flash("Producto agregado", "success")
    return redirect(url_for("productos"))


@app.route("/productos/editar/<id>", methods=["GET", "POST"])
def productos_editar(id):
    if request.method == "GET":
        p = fu.get_doc("productos", id)
        if not p:
            flash("Producto no encontrado", "warning")
            return redirect(url_for("productos"))
        return render_template("editar_producto.html", producto=p)

    nombre = request.form.get("nombre", "").strip()
    laboratorio = request.form.get("laboratorio", "").strip()
    try:
        precio = float(request.form.get("precio", "0"))
        stock = int(request.form.get("stock", "0"))
    except:
        flash("Precio/stock inválido", "danger")
        return redirect(url_for("productos"))
    fu.update("productos", id, {"nombre": nombre, "laboratorio": laboratorio, "precio": precio, "stock": stock})
    flash("Producto actualizado", "success")
    return redirect(url_for("productos"))


@app.route("/productos/eliminar/<id>")
def productos_eliminar(id):
    fu.delete("productos", id)
    flash("Producto eliminado", "warning")
    return redirect(url_for("productos"))


# ---------------- Crear Pedido ----------------
@app.route("/crear_pedido")
def crear_pedido():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "", type=str).strip()
    per_page = PER_PAGE

    clientes_all = fu.get_all("clientes")
    productos_all = fu.get_all("productos")

    if search:
        productos_all = [p for p in productos_all if search.lower() in p.get("nombre", "").lower()]

    # NOTE: enviamos productos_all a la plantilla para que el <select> muestre TODOS los productos,
    # mientras que las variables de paginación siguen calculadas sobre productos_all
    total = len(productos_all)
    pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    productos_page = productos_all[start:end]

    return render_template("crear_pedido.html",
                           clientes=clientes_all,
                           productos=productos_all,   # <-- todos los productos (para el select)
                           productos_page=productos_page,  # opcional: si quieres mostrar una lista paginada en la UI
                           page=page,
                           pages=pages,
                           per_page=per_page,
                           total=total,
                           search=search)


@app.route("/guardar_pedido", methods=["POST"])
def guardar_pedido():
    cliente_id = request.form.get("cliente_id")
    cart_json = request.form.get("cart_json", "[]")
    try:
        cart = json.loads(cart_json)
    except:
        cart = []

    if not cliente_id:
        flash("Selecciona un cliente antes de generar el pedido.", "danger")
        return redirect(url_for("crear_pedido"))

    if not cart:
        flash("El carrito está vacío.", "warning")
        return redirect(url_for("crear_pedido"))

    cliente = fu.get_doc("clientes", cliente_id)
    if not cliente:
        flash("Cliente inválido.", "danger")
        return redirect(url_for("crear_pedido"))

    items = []
    descontar = []
    total = 0.0
    for it in cart:
        pid = it.get("id")
        qty = int(it.get("cantidad", 0))
        if qty <= 0:
            continue
        prod = fu.get_doc("productos", pid)
        if not prod:
            flash(f"Producto con id {pid} no existe.", "danger")
            return redirect(url_for("crear_pedido"))
        if qty > int(prod.get("stock", 0)):
            flash(f"No hay stock suficiente para {prod.get('nombre')}.", "danger")
            return redirect(url_for("crear_pedido"))
        subtotal = float(prod.get("precio", 0)) * qty
        items.append({
            "id": pid,
            "nombre": prod.get("nombre"),
            "laboratorio": prod.get("laboratorio", ""),
            "cantidad": qty,
            "precio": prod.get("precio"),
            "subtotal": subtotal
        })
        descontar.append({"id": pid, "cantidad": qty})
        total += subtotal

    pedido_id = fu.guardar_pedido(cliente_id, cliente, items, total)
    fu.descontar_inventario(descontar)

    pdf_name = f"pedido_{pedido_id}.pdf"
    pdf_path = os.path.join(STATIC_DIR, pdf_name)
    try:
        generar_pdf(pdf_path, cliente, items, total)
        return send_file(pdf_path, as_attachment=True)
    except Exception as e:
        flash("Pedido guardado, pero no se pudo generar PDF: " + str(e), "warning")
        return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)












