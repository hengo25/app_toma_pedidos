const userId = 'usuario123';
let priceList = {};

function setMessage(text, type = "info") {
  const msg = document.getElementById('msg');
  msg.textContent = text;
  msg.className = `has-text-${type}`;
}

async function loadPrices() {
  try {
    const res = await fetch('/prices');
    priceList = await res.json();
    console.log("Precios cargados:", priceList);
  } catch (err) {
    console.error("Error al obtener precios:", err);
    priceList = {};
  }
}

async function getCart() {
  await loadPrices();
  const res = await fetch(`/cart/${userId}`);
  const data = await res.json();

  const list = document.getElementById('cart_list');
  list.innerHTML = '';

  let totalGeneral = 0;

  for (const [id, qty] of Object.entries(data)) {
    const precio = priceList[id] ?? 0;
    const subtotal = qty * precio;
    totalGeneral += subtotal;

    const li = document.createElement('li');
    li.innerHTML = `
      ${id}: ${qty} × $${precio.toFixed(2)} = <b>$${subtotal.toFixed(2)}</b>
    `;
    const btn = document.createElement('button');
    btn.textContent = '✖';
    btn.className = 'delete';
    btn.onclick = () => deleteItem(id);
    li.appendChild(btn);
    list.appendChild(li);
  }

  document.getElementById('total').textContent = `$${totalGeneral.toFixed(2)}`;
}

async function addToCart() {
  const id = document.getElementById('product_id').value.trim();
  const qty = +document.getElementById('qty').value;

  if (!id || qty <= 0) {
    return setMessage('ID inválido o cantidad ≤ 0', 'danger');
  }

  console.log("Enviando:", { product_id: id, qty: qty });

  try {
    const res = await fetch(`/cart/${userId}/item`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }, // ✅ Cabecera clave
      body: JSON.stringify({ product_id: id, qty: qty })
    });

    console.log("Respuesta status:", res.status);
    const text = await res.text();
    console.log("Respuesta cuerpo:", text);

    if (res.ok) {
      setMessage('✔ Artículo agregado', 'success');
      getCart();
    } else {
      try {
        const err = JSON.parse(text);
        setMessage(`❌ ${err.message}`, 'danger');
      } catch {
        setMessage(`❌ Error ${res.status}`, 'danger');
      }
    }
  } catch (error) {
    console.error('Fetch error:', error);
    setMessage('❌ Error de conexión', 'danger');
  }
}

async function deleteItem(id) {
  await fetch(`/cart/${userId}/item`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ product_id: id })
  });
  setMessage('Artículo eliminado', 'warning');
  getCart();
}

async function clearCart() {
  if (!confirm('¿Vaciar todo el carrito?')) return;
  await fetch(`/cart/${userId}`, { method: 'DELETE' });
  setMessage('Carrito vaciado', 'warning');
  getCart();
}

document.addEventListener('DOMContentLoaded', getCart);
