const DEFAULT_BASE_URL = 'http://127.0.0.1:8000'

export const API_BASE_URL = (
  import.meta.env.DEPLOYED_SERVER_URL ||
  import.meta.env.VITE_DEPLOYED_SERVER_URL ||
  import.meta.env.VITE_API_BASE_URL ||
  DEFAULT_BASE_URL
).replace(/\/+$/, '')

const TOKEN_KEY = 'lumoura_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token)
  }
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

function buildUrl(path) {
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`
}

async function parseError(response) {
  const fallback = `Request failed with status ${response.status}`
  try {
    const body = await response.json()
    return body.detail || body.message || fallback
  } catch {
    return fallback
  }
}

export async function apiRequest(path, { token, method = 'GET', body, headers } = {}) {
  const response = await fetch(buildUrl(path), {
    method,
    headers: {
      ...(body ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: body ? JSON.stringify(body) : undefined,
  })

  if (!response.ok) {
    throw new Error(await parseError(response))
  }

  const text = await response.text()
  return text ? JSON.parse(text) : null
}

export function joinUrl(path) {
  return buildUrl(path)
}
