import os
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

CRED_FILE = os.path.join(os.getcwd(), "credenciales.json")
if not os.path.exists(CRED_FILE):
    raise FileNotFoundError(f"No encontré 'credenciales.json' en {os.getcwd()}")

if not firebase_admin._apps:
    cred = credentials.Certificate(CRED_FILE)
    firebase_admin.initialize_app(cred)

db = firestore.client()

def _normalize_product(d: dict):
    if "precio" in d:
        try:
            d["precio"] = float(d["precio"])
        except:
            d["precio"] = 0.0
    if "stock" in d:
        try:
            d["stock"] = int(d["stock"])
        except:
            d["stock"] = 0
    return d

# CRUD genérico
def add(collection: str, data: dict):
    ref = db.collection(collection).document()
    ref.set(data)
    return ref.id

def get_all(collection: str):
    """
    Obtiene todos los documentos de la colección.
    Para productos aplica normalización de precio y stock.
    """
    docs = db.collection(collection).order_by("nombre").stream()
    out = []
    for d in docs:
        obj = d.to_dict()
        obj["id"] = d.id
        if collection == "productos":
            obj = _normalize_product(obj)
        out.append(obj)
    return out

def get_doc(collection: str, doc_id: str):
    doc = db.collection(collection).document(doc_id).get()
    if not doc.exists:
        return None
    obj = doc.to_dict()
    obj["id"] = doc.id
    if collection == "productos":
        obj = _normalize_product(obj)
    return obj

def update(collection: str, doc_id: str, data: dict):
    db.collection(collection).document(doc_id).update(data)

def delete(collection: str, doc_id: str):
    db.collection(collection).document(doc_id).delete()

# Pedidos
def guardar_pedido(cliente_id: str, cliente_data: dict, items: list, total: float):
    """
    Guarda un pedido con datos del cliente, items y total.
    """
    doc_ref = db.collection("pedidos").document()
    payload = {
        "cliente_id": cliente_id,
        "cliente": cliente_data,
        "items": items,
        "total": float(total),
        "fecha": datetime.utcnow().isoformat()
    }
    doc_ref.set(payload)
    return doc_ref.id

def descontar_inventario(items: list):
    """
    Descuenta inventario de los productos según la cantidad pedida.
    items = [{'id': <producto_id>, 'cantidad': <int>}, ...]
    """
    for it in items:
        pid = it["id"]
        cant = int(it["cantidad"])
        ref = db.collection("productos").document(pid)
        snap = ref.get()
        if not snap.exists:
            continue
        data = snap.to_dict()
        current = int(data.get("stock", 0))
        new_stock = max(0, current - cant)
        ref.update({"stock": new_stock})
