import { useEffect, useState } from 'react'
import {
  checkHealth,
  uploadDocuments,
  clearLibrary,
  askQuestion,
  exportAnnotatedPdf,
} from './lib/api'
import Header from './components/Header'
import Library from './components/Library'
import AskPanel from './components/AskPanel'
import ResultPanel from './components/ResultPanel'

function App() {
  const [backendOnline, setBackendOnline] = useState(null)

  const [documents, setDocuments] = useState([])
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  const [clearing, setClearing] = useState(false)
  const [clearError, setClearError] = useState(null)

  const [asking, setAsking] = useState(false)
  const [askError, setAskError] = useState(null)
  const [askResult, setAskResult] = useState(null)
  const [askedQuestion, setAskedQuestion] = useState('')

  const [exportDoc, setExportDoc] = useState('')
  const [exporting, setExporting] = useState(false)
  const [exportError, setExportError] = useState(null)

  useEffect(() => {
    checkHealth()
      .then(() => setBackendOnline(true))
      .catch(() => setBackendOnline(false))
  }, [])

  const handleUpload = async (files) => {
    setUploading(true)
    setUploadError(null)
    try {
      const uploaded = await uploadDocuments(files)
      setDocuments((prev) => {
        const byName = new Map(prev.map((d) => [d.document_name, d]))
        for (const doc of uploaded) byName.set(doc.document_name, doc)
        return [...byName.values()]
      })
    } catch (err) {
      setUploadError(err.message)
    } finally {
      setUploading(false)
    }
  }

  const handleClear = async () => {
    setClearing(true)
    setClearError(null)
    try {
      await clearLibrary()
      setDocuments([])
      setAskResult(null)
    } catch (err) {
      setClearError(err.message)
    } finally {
      setClearing(false)
    }
  }

  const handleAsk = async (question) => {
    setAsking(true)
    setAskError(null)
    setAskResult(null)
    try {
      const result = await askQuestion(question)
      setAskResult(result)
      setAskedQuestion(question)
      setExportError(null)

      const counts = {}
      for (const c of result.citations) {
        counts[c.document_name] = (counts[c.document_name] || 0) + 1
      }
      const ranked = Object.keys(counts).sort((a, b) => counts[b] - counts[a])
      setExportDoc(ranked[0] || '')
    } catch (err) {
      setAskError(err.message)
    } finally {
      setAsking(false)
    }
  }

  const handleExport = async (question, result) => {
    setExporting(true)
    setExportError(null)
    try {
      const blob = await exportAnnotatedPdf({ documentName: exportDoc, question, askResult: result })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${exportDoc}_annotated.pdf`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (err) {
      setExportError(err.message)
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="min-h-screen bg-paper">
      <Header />

      <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
        <div className="grid grid-cols-1 gap-6 md:grid-cols-[280px_1fr]">
          <Library
            documents={documents}
            onUpload={handleUpload}
            onClear={handleClear}
            uploading={uploading}
            clearing={clearing}
            uploadError={uploadError}
            clearError={clearError}
          />

          <div className="space-y-6">
            <AskPanel
              onAsk={handleAsk}
              asking={asking}
              error={askError}
              hasDocuments={documents.length > 0}
            />

            {askResult && (
              <ResultPanel
                question={askedQuestion}
                result={askResult}
                exportDoc={exportDoc}
                onExportDocChange={setExportDoc}
                onExport={handleExport}
                exporting={exporting}
                exportError={exportError}
              />
            )}
          </div>
        </div>
      </main>

      <footer className="mx-auto max-w-5xl px-4 py-6 text-xs text-ink-muted sm:px-6">
        <span
          className={`mr-1.5 inline-block h-1.5 w-1.5 rounded-full align-middle ${
            backendOnline ? 'bg-accent' : 'bg-ink-muted'
          }`}
          aria-hidden="true"
        />
        Backend {backendOnline === null ? 'checking…' : backendOnline ? 'connected' : 'unreachable'}
      </footer>
    </div>
  )
}

export default App
