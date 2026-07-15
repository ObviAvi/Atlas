'use client'

import { useState } from 'react'
import { queryLibrarian, LibrarianQueryResponse } from '@/lib/api'
import { Send, Loader2, BookOpen } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import LibrarianSources from '@/components/LibrarianSources'

export default function LibrarianTab() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState<LibrarianQueryResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setError(null)
    setResponse(null)

    try {
      const result = await queryLibrarian({ query: query.trim() })
      setResponse(result)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to query the Knowledge Graph')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="font-display text-3xl md:text-4xl text-walnut-900">The Librarian</h2>
          <p className="mt-2 text-sm text-walnut-600 max-w-xl">
            Ask questions about your company data. Answers are grounded in ingested documents
            and the knowledge graph — sources are available below if you want to dig deeper.
          </p>
        </div>
        <BookOpen className="text-walnut-400 hidden md:block" size={36} />
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="query" className="block text-[11px] uppercase tracking-[0.14em] text-walnut-500 mb-2">
            Your question
          </label>
          <textarea
            id="query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Who is working on Project Alpha? What is the status of Project Beta?"
            className="input-field"
            rows={3}
            disabled={loading}
          />
        </div>

        <button type="submit" disabled={loading || !query.trim()} className="btn-primary w-full md:w-auto">
          {loading ? (
            <>
              <Loader2 className="animate-spin" size={18} />
              Querying…
            </>
          ) : (
            <>
              <Send size={18} />
              Ask Librarian
            </>
          )}
        </button>
      </form>

      {error && (
        <div className="rounded-2xl border border-red-200/60 bg-red-50/80 p-4">
          <p className="text-red-900 font-medium text-sm">Error</p>
          <p className="text-red-700 text-sm mt-1">{error}</p>
        </div>
      )}

      {response && (
        <div className="space-y-4 animate-fade-in">
          <div className="rounded-2xl border border-walnut-700/10 bg-white/60 p-6">
            <p className="text-[11px] uppercase tracking-[0.14em] text-walnut-500 mb-3">Answer</p>
            <div className="text-walnut-700 leading-relaxed [&_p]:mb-3 [&_strong]:text-walnut-900 [&_ul]:list-disc [&_ul]:pl-5">
              <ReactMarkdown>{response.answer}</ReactMarkdown>
            </div>
          </div>

          {response.sources && response.sources.length > 0 && (
            <LibrarianSources sources={response.sources} />
          )}
        </div>
      )}
    </div>
  )
}

// Made with Bob
