import os
import json
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# Leer credenciales desde variable de entorno
credenciales_json = os.environ.get("FIREBASE_CREDENTIALS")

if not credenciales_json:
    raise FileNotFoundError("No encontré la variable de entorno FIREBASE_CREDENTIALS en Render")

# Convertir string JSON en diccionario
cred_dict = json.loads(credenciales_json)

# Inicializar Firebase solo si no está inicializado
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

# Cliente de Firestore
db = firestore.client()


# ----------------------------
# Funciones auxiliares
# ----------------------------
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


# ----------------------------
# CRUD genérico
# ----------------------------
def add(collection: str, data: dict):
    ref = db.collection(collection).document()
    ref.set(data)
    return ref.id

def get_all(collection: str):
    """
    Obtiene TODOS los documentos de la colección.
    La paginación se hace en Flask, NO en Firebase.
    """
    try:
        docs = db.collection(collection).stream()  # 👈 SIN order_by NI limit
        out = []
        for d in docs:
            obj = d.to_dict()
            obj["id"] = d.id
            if collection == "productos":
                obj = _normalize_product(obj)
            out.append(obj)
        return out
    except Exception as e:
        print("🔥 ERROR get_all:", collection, e)
        return []


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


# ----------------------------
# Pedidos
# ----------------------------
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
















