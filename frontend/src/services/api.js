const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })

  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || `Request failed with ${response.status}`)
  }

  return response.json()
}

function withQuery(path, params) {
  const query = new URLSearchParams()
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, value)
    }
  })
  const suffix = query.toString()
  return suffix ? `${path}?${suffix}` : path
}

export const api = {
  dashboard: () => request('/dashboard/summary'),
  shipments: (params) => request(withQuery('/shipments/', params)),
  shipment: (id) => request(`/shipments/${id}`),
  updateShipment: (id, payload) =>
    request(`/shipments/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),
  products: (params) => request(withQuery('/products/', params)),
  predictions: () => request('/predictions/'),
  runDelayPrediction: (id) => request(`/predictions/delay/${id}`, { method: 'POST' }),
  runCostPrediction: (id) => request(`/predictions/cost/${id}`, { method: 'POST' }),
  runStockPrediction: (id) => request(`/predictions/stock/${id}`, { method: 'POST' }),
  alerts: (params) => request(withQuery('/alerts/', params)),
  resolveAlert: (id) => request(`/alerts/${id}/resolve`, { method: 'PATCH' }),
}
