'use client'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import dynamic from 'next/dynamic'
import {
  getGraphData,
  getGraphStatus,
  uploadDocument,
  listDocuments,
  deleteDocument,
  GraphLink,
  GraphNode,
  GraphVisualizationResponse,
  IngestedDocument,
} from '@/lib/api'
import { FileText, Loader2, Maximize2, Network, Plus, RefreshCw, Trash2, Upload, X } from 'lucide-react'

const ACCEPTED_UPLOAD_EXTENSIONS = ['.txt', '.md', '.markdown', '.text']

function hasAcceptedExtension(name: string): boolean {
  const lower = name.toLowerCase()
  return ACCEPTED_UPLOAD_EXTENSIONS.some((ext) => lower.endsWith(ext))
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), { ssr: false })

// Luminous, warm palette tuned to read against the deep graph canvas.
const NODE_COLORS: Record<string, string> = {
  Employee: '#F2D8A7',
  Project: '#E39A5B',
  Department: '#C77D48',
  Client: '#EAD3AC',
  OKR: '#D4B483',
  Budget: '#B5895A',
  Document: '#8C7A63',
  Entity: '#9C8B7A',
}

const DIM_NODE_COLOR = '#2A2018'
const SELECTED_NODE_COLOR = '#FFF7E8'

const LINK_COLOR = '#C9B790'
const LINK_COLOR_ACTIVE = '#FFE9BE'
const LINK_COLOR_DIM = '#4A3B2C'
const PARTICLE_COLOR = '#FFD98A'

const HIDDEN_PROPERTY_KEYS = new Set(['embedding'])
const LABEL_MAX_LENGTH = 48
const DOCUMENT_TEXT_MAX_LENGTH = 180
const DEFAULT_PROPERTY_MAX_LENGTH = 240

function truncateText(value: string, maxLength: number): string {
  if (value.length <= maxLength) return value
  return `${value.slice(0, maxLength).trim()}…`
}

function formatPropertyValue(key: string, value: unknown, nodeType: string): string {
  if (value == null) return '—'
  const str = String(value)

  if (key === 'text' || (nodeType === 'Document' && str.length > DOCUMENT_TEXT_MAX_LENGTH)) {
    return truncateText(str, DOCUMENT_TEXT_MAX_LENGTH)
  }

  if (str.length > DEFAULT_PROPERTY_MAX_LENGTH) {
    return truncateText(str, DEFAULT_PROPERTY_MAX_LENGTH)
  }

  return str
}

function getVisibleProperties(properties: Record<string, unknown>) {
  return Object.entries(properties).filter(([key]) => !HIDDEN_PROPERTY_KEYS.has(key))
}

function linkEndId(end: unknown): string {
  if (end && typeof end === 'object' && 'id' in (end as Record<string, unknown>)) {
    return String((end as { id: unknown }).id)
  }
  return String(end)
}

function linkKey(link: { source: unknown; target: unknown }): string {
  return `${linkEndId(link.source)}->${linkEndId(link.target)}`
}

export default function GraphExplorerTab({ active = true }: { active?: boolean }) {
  const graphRef = useRef<any>(null)
  const [graphData, setGraphData] = useState<GraphVisualizationResponse | null>(null)
  const [status, setStatus] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [highlightNodeIds, setHighlightNodeIds] = useState<Set<string>>(new Set())
  const [highlightLinkKeys, setHighlightLinkKeys] = useState<Set<string>>(new Set())
  const [dimensions, setDimensions] = useState({ width: 1200, height: 800 })

  const [showIngest, setShowIngest] = useState(false)
  const [docTitle, setDocTitle] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [clearOnIngest, setClearOnIngest] = useState(false)
  const [ingesting, setIngesting] = useState(false)
  const [ingestMessage, setIngestMessage] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [documents, setDocuments] = useState<IngestedDocument[]>([])
  const [deletingTitle, setDeletingTitle] = useState<string | null>(null)
  const [confirmTitle, setConfirmTitle] = useState<string | null>(null)

  const loadGraph = useCallback(async () => {
    setLoading(true)
    setError(null)
    setSelectedNode(null)
    setHighlightNodeIds(new Set())
    setHighlightLinkKeys(new Set())
    try {
      const [data, stats, docs] = await Promise.all([getGraphData(), getGraphStatus(), listDocuments()])
      setGraphData(data)
      setStatus(stats)
      setDocuments(docs.documents)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load Knowledge Graph')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadGraph()
  }, [loadGraph])

  useEffect(() => {
    const updateSize = () => {
      setDimensions({ width: window.innerWidth, height: window.innerHeight })
    }
    updateSize()
    window.addEventListener('resize', updateSize)
    return () => window.removeEventListener('resize', updateSize)
  }, [])

  // Degree map drives node size, so busy hubs read larger — like the reference.
  const degreeMap = useMemo(() => {
    const counts: Record<string, number> = {}
    graphData?.links.forEach((l) => {
      const s = linkEndId(l.source)
      const t = linkEndId(l.target)
      counts[s] = (counts[s] || 0) + 1
      counts[t] = (counts[t] || 0) + 1
    })
    return counts
  }, [graphData])

  const forceData = useMemo(() => {
    if (!graphData) return { nodes: [], links: [] }
    return {
      nodes: graphData.nodes.map((n) => ({ ...n })),
      links: graphData.links.map((l: GraphLink) => ({ ...l })),
    }
  }, [graphData])

  const typeCounts = useMemo(() => {
    if (!graphData) return []
    const counts: Record<string, number> = {}
    graphData.nodes.forEach((n) => {
      counts[n.type] = (counts[n.type] || 0) + 1
    })
    return Object.entries(counts).sort((a, b) => b[1] - a[1])
  }, [graphData])

  const selectedNodeProperties = useMemo(
    () => (selectedNode ? getVisibleProperties(selectedNode.properties) : []),
    [selectedNode],
  )

  const hasSelection = highlightNodeIds.size > 0

  const focusNode = useCallback((node: any) => {
    const g = graphRef.current
    if (!g || typeof node.x !== 'number') return
    const distance = 160
    const hyp = Math.hypot(node.x, node.y, node.z) || 1
    const ratio = 1 + distance / hyp
    g.cameraPosition(
      { x: node.x * ratio, y: node.y * ratio, z: node.z * ratio },
      node,
      900,
    )
  }, [])

  const handleNodeClick = useCallback(
    (node: any) => {
      setSelectedNode(node as GraphNode)

      const neighbors = new Set<string>([String(node.id)])
      const links = new Set<string>()
      graphData?.links.forEach((l) => {
        const s = linkEndId(l.source)
        const t = linkEndId(l.target)
        if (s === String(node.id) || t === String(node.id)) {
          neighbors.add(s)
          neighbors.add(t)
          links.add(`${s}->${t}`)
        }
      })
      setHighlightNodeIds(neighbors)
      setHighlightLinkKeys(links)
      focusNode(node)
    },
    [graphData, focusNode],
  )

  const clearSelection = useCallback(() => {
    setSelectedNode(null)
    setHighlightNodeIds(new Set())
    setHighlightLinkKeys(new Set())
  }, [])

  const resetView = useCallback(() => {
    clearSelection()
    graphRef.current?.zoomToFit(700, 60)
  }, [clearSelection])

  const selectFile = useCallback((file: File | null) => {
    setIngestMessage(null)
    if (!file) {
      setSelectedFile(null)
      return
    }
    if (!hasAcceptedExtension(file.name)) {
      setSelectedFile(null)
      setIngestMessage(`Unsupported file type. Accepted: ${ACCEPTED_UPLOAD_EXTENSIONS.join(', ')}`)
      return
    }
    setSelectedFile(file)
    // Default the title to the filename (without extension) when none is set yet.
    if (!docTitle.trim()) {
      setDocTitle(file.name.replace(/\.[^./\\]+$/, ''))
    }
  }, [docTitle])

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    selectFile(e.target.files?.[0] ?? null)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
    selectFile(e.dataTransfer.files?.[0] ?? null)
  }

  const handleIngest = async () => {
    if (!selectedFile) return
    setIngesting(true)
    setIngestMessage(null)
    try {
      const result = await uploadDocument(selectedFile, {
        title: docTitle.trim() || undefined,
        clearExisting: clearOnIngest,
      })
      setIngestMessage(result.message)
      setSelectedFile(null)
      setDocTitle('')
      if (fileInputRef.current) fileInputRef.current.value = ''
      await loadGraph()
    } catch (err: any) {
      setIngestMessage(err.response?.data?.detail || 'Ingestion failed')
    } finally {
      setIngesting(false)
    }
  }

  const handleDeleteDocument = async (title: string) => {
    // Two-step confirm: first click arms, second click deletes.
    if (confirmTitle !== title) {
      setConfirmTitle(title)
      return
    }
    setConfirmTitle(null)
    setDeletingTitle(title)
    setIngestMessage(null)
    try {
      const result = await deleteDocument(title)
      setIngestMessage(result.message)
      await loadGraph()
    } catch (err: any) {
      setIngestMessage(err.response?.data?.detail || 'Delete failed')
    } finally {
      setDeletingTitle(null)
    }
  }

  const nodeColor = useCallback(
    (node: any) => {
      const base = NODE_COLORS[node.type] || NODE_COLORS.Entity
      if (!hasSelection) return base
      if (String(node.id) === String(selectedNode?.id)) return SELECTED_NODE_COLOR
      if (highlightNodeIds.has(String(node.id))) return base
      return DIM_NODE_COLOR
    },
    [hasSelection, highlightNodeIds, selectedNode],
  )

  const nodeVal = useCallback(
    (node: any) => {
      const base = 1 + (degreeMap[String(node.id)] || 0) * 0.9
      return String(node.id) === String(selectedNode?.id) ? base * 2.4 : base
    },
    [degreeMap, selectedNode],
  )

  const linkColor = useCallback(
    (link: any) => {
      if (!hasSelection) return LINK_COLOR
      return highlightLinkKeys.has(linkKey(link)) ? LINK_COLOR_ACTIVE : LINK_COLOR_DIM
    },
    [hasSelection, highlightLinkKeys],
  )

  const linkWidth = useCallback(
    (link: any) => (highlightLinkKeys.has(linkKey(link)) ? 1.8 : 0.4),
    [highlightLinkKeys],
  )

  const linkParticles = useCallback(
    (link: any) => {
      if (!hasSelection) return 1
      return highlightLinkKeys.has(linkKey(link)) ? 4 : 0
    },
    [hasSelection, highlightLinkKeys],
  )

  const isEmpty = !loading && !error && forceData.nodes.length === 0

  return (
    <div
      className="fixed inset-0 z-0"
      style={{
        background: 'radial-gradient(circle at 50% 42%, #241a12 0%, #1a1612 48%, #100b08 100%)',
      }}
    >
      {/* The 3D graph itself — always mounted so it stays a seamless backdrop across tabs */}
      <div className={active ? '' : 'pointer-events-none'}>
        {!error && forceData.nodes.length > 0 && (
          <ForceGraph3D
            ref={graphRef}
            graphData={forceData}
            width={dimensions.width}
            height={dimensions.height}
            backgroundColor="rgba(0,0,0,0)"
            showNavInfo={false}
            nodeLabel={(node: any) => `${node.type}: ${node.label}`}
            nodeColor={nodeColor}
            nodeVal={nodeVal}
            nodeOpacity={0.95}
            nodeResolution={16}
            linkColor={linkColor}
            linkWidth={linkWidth}
            linkOpacity={0.4}
            linkDirectionalParticles={linkParticles}
            linkDirectionalParticleWidth={1.8}
            linkDirectionalParticleSpeed={0.006}
            linkDirectionalParticleColor={() => PARTICLE_COLOR}
            onNodeClick={handleNodeClick}
            onBackgroundClick={clearSelection}
            cooldownTicks={120}
            onEngineStop={() => graphRef.current?.zoomToFit(600, 60)}
          />
        )}
      </div>

      {/* Soft inner vignette so the graph melts into the window edges */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{ boxShadow: 'inset 0 0 200px 60px rgba(16, 11, 8, 0.9)' }}
      />

      {/* Everything below is the Atlas HUD — only shown/active on the Atlas tab */}
      {active && (
        <>
          {/* Loading state */}
          {loading && (
            <div className="absolute inset-0 z-20 flex flex-col items-center justify-center">
              <Loader2 className="animate-spin text-cream/80 mb-3" size={32} />
              <p className="text-sm text-cream/70">Loading graph from Neo4j…</p>
            </div>
          )}

          {/* Error state */}
          {error && (
            <div className="absolute inset-0 z-20 flex items-center justify-center p-8">
              <div className="text-center">
                <p className="text-cream font-medium mb-2">Could not load graph</p>
                <p className="text-sm text-cream/60">{error}</p>
              </div>
            </div>
          )}

          {/* Empty state */}
          {isEmpty && (
            <div className="absolute inset-0 z-20 flex flex-col items-center justify-center p-8 text-center">
              <Network className="text-cream/40 mb-4" size={44} />
              <p className="font-display text-xl text-cream mb-2">No data yet</p>
              <p className="text-sm text-cream/60">Add a document to populate the graph.</p>
            </div>
          )}

          {/* HUD: title + counts (top-left) */}
          {!loading && !error && !isEmpty && (
            <div className="pointer-events-none absolute left-5 top-24 z-10 rounded-2xl border border-white/10 bg-walnut-900/50 px-4 py-3 backdrop-blur-md">
              <p className="text-[10px] uppercase tracking-[0.16em] text-cream/50">Knowledge graph</p>
              <div className="mt-1 flex items-baseline gap-3">
                <span className="font-display text-2xl text-cream">{status?.total_nodes ?? '—'}</span>
                <span className="text-[11px] uppercase tracking-wider text-cream/50">nodes</span>
                <span className="font-display text-2xl text-cream">{status?.total_relationships ?? '—'}</span>
                <span className="text-[11px] uppercase tracking-wider text-cream/50">links</span>
              </div>
              {status?.documents && (
                <p className="mt-1 text-[11px] text-cream/40">
                  {status.documents.embedded_documents ?? 0} / {status.documents.total_documents ?? 0} documents embedded
                </p>
              )}
            </div>
          )}

          {/* HUD: view controls (top-right) */}
          {!loading && !error && (
            <div className="pointer-events-auto absolute right-5 top-24 z-10 flex gap-2">
              <button
                onClick={resetView}
                disabled={isEmpty}
                title="Reset view"
                className="flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-walnut-900/50 text-cream/80 backdrop-blur-md transition-colors hover:bg-walnut-900/70 hover:text-cream disabled:opacity-40"
              >
                <Maximize2 size={16} />
              </button>
              <button
                onClick={loadGraph}
                title="Refresh"
                className="flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-walnut-900/50 text-cream/80 backdrop-blur-md transition-colors hover:bg-walnut-900/70 hover:text-cream"
              >
                {loading ? <Loader2 className="animate-spin" size={16} /> : <RefreshCw size={16} />}
              </button>
            </div>
          )}

          {/* HUD: legend (bottom-left) */}
          {!loading && !error && typeCounts.length > 0 && (
            <div className="pointer-events-none absolute bottom-5 left-5 z-10 max-w-[240px] rounded-2xl border border-white/10 bg-walnut-900/50 px-4 py-3 backdrop-blur-md">
              <p className="mb-2 text-[10px] uppercase tracking-[0.16em] text-cream/50">Entity types</p>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
                {typeCounts.map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between gap-2 text-xs">
                    <span className="flex items-center gap-2 min-w-0">
                      <span
                        className="h-2.5 w-2.5 shrink-0 rounded-full"
                        style={{ backgroundColor: NODE_COLORS[type] || NODE_COLORS.Entity }}
                      />
                      <span className="truncate text-cream/80">{type}</span>
                    </span>
                    <span className="text-cream/45">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* HUD: interaction hint (bottom-right) */}
          {!loading && !error && !isEmpty && (
            <div className="pointer-events-none absolute bottom-6 right-5 z-10 hidden text-[11px] uppercase tracking-[0.14em] text-cream/40 md:block">
              Drag to rotate · Scroll to zoom · Right-drag to pan
            </div>
          )}

          {/* HUD: selected node detail (right) */}
          {selectedNode && (
            <div className="pointer-events-auto absolute right-5 top-40 z-10 w-[300px] max-w-[calc(100%-2.5rem)] rounded-2xl border border-white/10 bg-walnut-900/70 p-5 backdrop-blur-lg animate-fade-in">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-[10px] uppercase tracking-[0.16em] text-cream/50">Selected node</p>
                  <p
                    className="mt-1 font-display text-lg text-cream leading-snug break-words"
                    title={selectedNode.label}
                  >
                    {truncateText(selectedNode.label, LABEL_MAX_LENGTH)}
                  </p>
                </div>
                <button
                  onClick={clearSelection}
                  className="shrink-0 rounded-full p-1 text-cream/50 transition-colors hover:bg-white/10 hover:text-cream"
                  aria-label="Clear selection"
                >
                  <X size={16} />
                </button>
              </div>
              <span
                className="mt-2 inline-flex w-fit items-center rounded-full border border-white/15 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.14em] text-cream/80"
                style={{ backgroundColor: `${NODE_COLORS[selectedNode.type] || NODE_COLORS.Entity}22` }}
              >
                {selectedNode.type}
              </span>
              {selectedNodeProperties.length > 0 && (
                <dl className="mt-4 max-h-[46vh] space-y-2 overflow-y-auto pr-1">
                  {selectedNodeProperties.map(([key, value]) => (
                    <div key={key}>
                      <dt className="text-[10px] uppercase tracking-wider text-cream/40">{key}</dt>
                      <dd
                        className="text-sm text-cream/85 break-words line-clamp-6"
                        title={String(value ?? '')}
                      >
                        {formatPropertyValue(key, value, selectedNode.type)}
                      </dd>
                    </div>
                  ))}
                </dl>
              )}
            </div>
          )}

          {/* HUD: ingest — collapsible bottom-center */}
          {!loading && !error && (
            <div className="pointer-events-none absolute inset-x-0 bottom-5 z-10 flex flex-col items-center gap-3 px-4">
              {showIngest && (
                <div className="pointer-events-auto w-full max-w-xl rounded-3xl border border-white/40 bg-cream/95 p-5 shadow-float backdrop-blur-xl animate-fade-up">
                  <div className="mb-3 flex items-start justify-between">
                    <div>
                      <p className="text-[11px] uppercase tracking-[0.14em] text-walnut-500">Add documents</p>
                      <p className="mt-1 text-sm text-walnut-600">
                        Extract entities into the graph and embed chunks for semantic search.
                      </p>
                    </div>
                    <button
                      onClick={() => setShowIngest(false)}
                      className="shrink-0 rounded-full p-1 text-walnut-400 transition-colors hover:bg-walnut-700/10 hover:text-walnut-700"
                      aria-label="Close"
                    >
                      <X size={18} />
                    </button>
                  </div>

                  {documents.length > 0 && (
                    <div className="mb-4">
                      <p className="mb-2 text-[11px] uppercase tracking-[0.14em] text-walnut-500">
                        Ingested documents
                      </p>
                      <ul className="max-h-40 space-y-1.5 overflow-y-auto pr-1">
                        {documents.map((doc) => {
                          const isDeleting = deletingTitle === doc.title
                          const isArmed = confirmTitle === doc.title
                          return (
                            <li
                              key={doc.title}
                              className="flex items-center justify-between gap-3 rounded-xl border border-walnut-700/10 bg-white/60 px-3 py-2"
                            >
                              <div className="flex min-w-0 items-center gap-2">
                                <FileText size={15} className="shrink-0 text-walnut-500" />
                                <div className="min-w-0">
                                  <p className="truncate text-sm text-walnut-800" title={doc.title}>
                                    {doc.title}
                                  </p>
                                  <p className="text-[11px] text-walnut-400">
                                    {doc.chunk_count} chunk{doc.chunk_count === 1 ? '' : 's'} · {doc.entity_count} entit
                                    {doc.entity_count === 1 ? 'y' : 'ies'}
                                  </p>
                                </div>
                              </div>
                              <button
                                type="button"
                                onClick={() => handleDeleteDocument(doc.title)}
                                onMouseLeave={() => isArmed && setConfirmTitle(null)}
                                disabled={isDeleting || (deletingTitle !== null && !isDeleting)}
                                title={isArmed ? 'Click again to confirm' : 'Delete document and its entities'}
                                className={`flex shrink-0 items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-40 ${
                                  isArmed
                                    ? 'bg-red-600 text-white hover:bg-red-700'
                                    : 'text-red-600 hover:bg-red-50'
                                }`}
                              >
                                {isDeleting ? (
                                  <Loader2 className="animate-spin" size={14} />
                                ) : (
                                  <Trash2 size={14} />
                                )}
                                {isDeleting ? 'Deleting' : isArmed ? 'Confirm' : 'Delete'}
                              </button>
                            </li>
                          )
                        })}
                      </ul>
                    </div>
                  )}

                  <div className="mb-3 grid grid-cols-1 items-center gap-3 sm:grid-cols-[1fr_auto]">
                    <input
                      type="text"
                      value={docTitle}
                      onChange={(e) => setDocTitle(e.target.value)}
                      placeholder="Document title (optional)"
                      className="input-field py-3"
                      disabled={ingesting}
                    />
                    <label className="flex items-center gap-2 whitespace-nowrap text-sm text-walnut-600">
                      <input
                        type="checkbox"
                        checked={clearOnIngest}
                        onChange={(e) => setClearOnIngest(e.target.checked)}
                        className="rounded border-walnut-300"
                        disabled={ingesting}
                      />
                      Replace existing graph
                    </label>
                  </div>

                  <input
                    ref={fileInputRef}
                    type="file"
                    accept={ACCEPTED_UPLOAD_EXTENSIONS.join(',')}
                    onChange={handleFileInputChange}
                    className="hidden"
                    disabled={ingesting}
                  />

                  <div
                    role="button"
                    tabIndex={0}
                    onClick={() => !ingesting && fileInputRef.current?.click()}
                    onKeyDown={(e) => {
                      if ((e.key === 'Enter' || e.key === ' ') && !ingesting) {
                        e.preventDefault()
                        fileInputRef.current?.click()
                      }
                    }}
                    onDragOver={(e) => {
                      e.preventDefault()
                      if (!ingesting) setDragActive(true)
                    }}
                    onDragLeave={() => setDragActive(false)}
                    onDrop={handleDrop}
                    className={`flex min-h-[120px] cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed px-5 py-6 text-center transition-colors ${
                      dragActive
                        ? 'border-walnut-500 bg-walnut-500/5'
                        : 'border-walnut-700/20 bg-white/50 hover:border-walnut-500/50 hover:bg-white/70'
                    } ${ingesting ? 'pointer-events-none opacity-60' : ''}`}
                  >
                    {selectedFile ? (
                      <>
                        <FileText size={22} className="text-walnut-600" />
                        <p className="text-sm font-medium text-walnut-800">{selectedFile.name}</p>
                        <p className="text-xs text-walnut-500">
                          {formatFileSize(selectedFile.size)} · click or drop to replace
                        </p>
                      </>
                    ) : (
                      <>
                        <Upload size={22} className="text-walnut-500" />
                        <p className="text-sm text-walnut-700">
                          Drag &amp; drop a document, or <span className="underline">browse</span>
                        </p>
                        <p className="text-xs text-walnut-400">
                          Accepts {ACCEPTED_UPLOAD_EXTENSIONS.join(', ')} files
                        </p>
                      </>
                    )}
                  </div>

                  <div className="mt-3 flex flex-wrap items-center gap-3">
                    <button
                      type="button"
                      onClick={handleIngest}
                      disabled={ingesting || !selectedFile}
                      className="btn-primary"
                    >
                      {ingesting ? <Loader2 className="animate-spin" size={16} /> : <Upload size={16} />}
                      Ingest document
                    </button>
                    {selectedFile && !ingesting && (
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedFile(null)
                          if (fileInputRef.current) fileInputRef.current.value = ''
                        }}
                        className="text-sm text-walnut-500 underline hover:text-walnut-700"
                      >
                        Remove
                      </button>
                    )}
                    {ingestMessage && <p className="text-sm text-walnut-600">{ingestMessage}</p>}
                  </div>
                </div>
              )}

              {!showIngest && (
                <button
                  onClick={() => setShowIngest(true)}
                  className="pointer-events-auto inline-flex items-center gap-2 rounded-full border border-white/10 bg-walnut-900/60 px-5 py-2.5 text-xs font-medium uppercase tracking-[0.12em] text-cream backdrop-blur-md transition-colors hover:bg-walnut-900/80"
                >
                  <Plus size={16} />
                  Add documents
                </button>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}

// Made with Bob
