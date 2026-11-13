// Local dev (`npm run dev`) talks to the backend directly on localhost:8000.
// The Docker build sets VITE_API_BASE=/api at build time so the same bundle
// instead calls through nginx's reverse proxy to the backend container.
export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

async function parseErrorMessage(res, fallback) {
  try {
    const data = await res.json()
    return data.detail || fallback
  } catch {
    return fallback
  }
}

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`)
  if (!res.ok) throw new Error(`unreachable (${res.status})`)
  const data = await res.json()
  return data.status
}

export async function uploadDocuments(files) {
  const formData = new FormData()
  for (const file of files) formData.append('files', file)

  const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: formData })
  if (!res.ok) {
    throw new Error(await parseErrorMessage(res, `Upload failed (${res.status}).`))
  }
  return res.json()
}

export async function fetchDocuments() {
  const res = await fetch(`${API_BASE}/documents`)
  if (!res.ok) {
    throw new Error(await parseErrorMessage(res, `Loading the library failed (${res.status}).`))
  }
  return res.json()
}

export async function clearLibrary() {
  const res = await fetch(`${API_BASE}/clear`, { method: 'DELETE' })
  if (!res.ok) {
    throw new Error(await parseErrorMessage(res, `Clearing the library failed (${res.status}).`))
  }
  return res.json()
}

export async function askQuestion(question, topK = 5) {
  const res = await fetch(`${API_BASE}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, top_k: topK }),
  })
  if (!res.ok) {
    throw new Error(await parseErrorMessage(res, `Asking failed (${res.status}).`))
  }
  return res.json()
}

export async function exportAnnotatedPdf({ documentName, question, askResult }) {
  const res = await fetch(`${API_BASE}/export`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      document_name: documentName,
      question,
      answer: askResult.answer,
      confidence: askResult.confidence,
      confidence_breakdown: askResult.confidence_breakdown,
      citations: askResult.citations,
    }),
  })
  if (!res.ok) {
    throw new Error(await parseErrorMessage(res, `Export failed (${res.status}).`))
  }
  return res.blob()
}

/** Turns a raw fetch/API error message into something a reader can act on. */
export function explainError(message) {
  if (!message) return null
  if (message.includes('ANTHROPIC_API_KEY')) {
    return {
      summary: "The backend isn't configured with an Anthropic API key yet.",
      detail: message,
    }
  }
  if (message.includes('unreachable') || message.includes('Failed to fetch')) {
    return {
      summary: "Can't reach the backend.",
      detail: 'Make sure the FastAPI server is running on http://localhost:8000.',
    }
  }
  return { summary: message, detail: null }
}
