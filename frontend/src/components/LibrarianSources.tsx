'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'

interface SourceItem {
  type?: string
  results?: any[]
  query?: string
  context?: string
  error?: string
}

const SOURCE_LABELS: Record<string, string> = {
  vector_search: 'Semantic matches',
  fulltext_search: 'Keyword matches',
  graph_expansion: 'Linked entities',
  cypher_query: 'Graph query',
  cypher_results: 'Query results',
}

function SourceBox({
  title,
  subtitle,
  children,
}: {
  title: string
  subtitle?: string
  children: React.ReactNode
}) {
  const [open, setOpen] = useState(false)

  return (
    <div className="rounded-xl border border-walnut-700/10 bg-white/80 overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between gap-3 px-4 py-3 text-left hover:bg-sand-50/80 transition-colors"
      >
        <div className="flex items-center gap-2 min-w-0">
          {open ? (
            <ChevronDown size={16} className="text-walnut-500 shrink-0" />
          ) : (
            <ChevronRight size={16} className="text-walnut-500 shrink-0" />
          )}
          <span className="font-medium text-sm text-walnut-800 truncate">{title}</span>
        </div>
        {subtitle && (
          <span className="text-xs text-walnut-400 shrink-0">{subtitle}</span>
        )}
      </button>
      {open && <div className="px-4 pb-4 border-t border-walnut-700/5">{children}</div>}
    </div>
  )
}

function ChunkPreview({ text, score }: { text: string; score?: number }) {
  const preview = text.trim().slice(0, 500)
  return (
    <div className="rounded-lg bg-sand-50/80 p-3 text-xs text-walnut-700 leading-relaxed">
      {typeof score === 'number' && (
        <p className="text-[10px] uppercase tracking-wider text-walnut-400 mb-2">
          Relevance {score.toFixed(3)}
        </p>
      )}
      <p className="whitespace-pre-wrap">{preview}{text.length > 500 ? '…' : ''}</p>
    </div>
  )
}

function EntityRow({ entity }: { entity: Record<string, unknown> }) {
  const name = String(entity.id || entity.name || 'Unknown')
  const type = String(entity.type || 'Entity')
  const extras = ['status', 'role', 'description', 'budget']
    .filter((k) => entity[k])
    .map((k) => `${k}: ${entity[k]}`)

  return (
    <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1 py-1.5 border-b border-walnut-700/5 last:border-0">
      <span className="pill-tag text-[10px] py-0.5">{type}</span>
      <span className="text-sm text-walnut-800 font-medium">{name}</span>
      {extras.length > 0 && (
        <span className="text-xs text-walnut-500">{extras.join(' · ')}</span>
      )}
    </div>
  )
}

export default function LibrarianSources({ sources }: { sources: SourceItem[] }) {
  if (!sources?.length) return null

  return (
    <div className="rounded-2xl border border-walnut-700/10 bg-sand-100/50 p-6">
      <p className="text-[11px] uppercase tracking-[0.14em] text-walnut-500 mb-3">Sources</p>
      <div className="space-y-2">
        {sources.map((source, index) => {
          const type = source.type || 'unknown'
          const label = SOURCE_LABELS[type] || type

          if (type === 'vector_search' || type === 'fulltext_search') {
            const results = source.results || []
            if (source.error) {
              return (
                <SourceBox key={index} title={label} subtitle="Error">
                  <p className="text-xs text-red-600">{source.error}</p>
                </SourceBox>
              )
            }
            return (
              <SourceBox key={index} title={label} subtitle={`${results.length} chunks`}>
                <div className="space-y-2 mt-3">
                  {results.map((hit: any, i: number) => (
                    <ChunkPreview key={i} text={hit.text || ''} score={hit.score} />
                  ))}
                </div>
              </SourceBox>
            )
          }

          if (type === 'graph_expansion') {
            const results = source.results || []
            return (
              <SourceBox key={index} title={label} subtitle={`${results.length} entities`}>
                <div className="mt-3">
                  {results.map((entity: any, i: number) => (
                    <EntityRow key={i} entity={entity} />
                  ))}
                </div>
              </SourceBox>
            )
          }

          if (type === 'cypher_query' && source.query) {
            return (
              <SourceBox key={index} title={label}>
                <pre className="mt-3 text-xs text-walnut-700 bg-sand-50/80 rounded-lg p-3 overflow-x-auto whitespace-pre-wrap font-mono">
                  {source.query}
                </pre>
              </SourceBox>
            )
          }

          if (type === 'cypher_results' && source.context) {
            return (
              <SourceBox key={index} title={label}>
                <pre className="mt-3 text-xs text-walnut-700 bg-sand-50/80 rounded-lg p-3 overflow-x-auto whitespace-pre-wrap">
                  {source.context}
                </pre>
              </SourceBox>
            )
          }

          return null
        })}
      </div>
    </div>
  )
}

// Made with Bob
