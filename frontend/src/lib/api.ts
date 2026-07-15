/**
 * API client for communicating with the FastAPI backend.
 */
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Types
export interface IngestRequest {
  text: string
  title?: string
  clear_existing?: boolean
}

export interface IngestResponse {
  status: string
  message: string
  nodes_created: number
  relationships_created: number
}

export interface IngestedDocument {
  title: string
  chunk_count: number
  entity_count: number
  embedded_count: number
}

export interface DeleteDocumentResponse {
  status: string
  message: string
  deleted_documents: number
  deleted_entities: number
}

export interface LibrarianQueryRequest {
  query: string
}

export interface LibrarianQueryResponse {
  query: string
  answer: string
  sources: any[]
}

export interface BoardroomDebateRequest {
  idea: string
  rounds?: number
}

export interface AgentMessage {
  agent: string
  message: string
  timestamp: string
}

export interface BoardroomStreamEvent {
  type: 'message' | 'complete' | 'error'
  agent?: string
  message?: string
  timestamp?: string
  node?: string
  round_count?: number
  final_verdict?: string
  data_sources?: string[]
  error?: string
}

export interface BoardroomStreamCallbacks {
  onMessage: (msg: AgentMessage & { round_count?: number }) => void
  onComplete: (result: { final_verdict: string; data_sources: string[] }) => void
  onError: (error: string) => void
}

export interface GraphNode {
  id: string
  label: string
  type: string
  properties: Record<string, unknown>
}

export interface GraphLink {
  source: string
  target: string
  type: string
  properties: Record<string, unknown>
}

export interface GraphVisualizationResponse {
  nodes: GraphNode[]
  links: GraphLink[]
  total_nodes: number
  total_relationships: number
}

// API Functions

/**
 * Ingest raw text into the Knowledge Graph
 */
export async function ingestData(request: IngestRequest): Promise<IngestResponse> {
  const response = await apiClient.post('/api/ingest/', request)
  return response.data
}

/**
 * Upload a text/Markdown document file and ingest it into the Knowledge Graph
 */
export async function uploadDocument(
  file: File,
  options: { title?: string; clearExisting?: boolean } = {},
): Promise<IngestResponse> {
  const formData = new FormData()
  formData.append('file', file)
  if (options.title) formData.append('title', options.title)
  formData.append('clear_existing', String(options.clearExisting ?? false))

  const response = await apiClient.post('/api/ingest/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

/**
 * Ingest all mock sample documents
 */
export async function ingestSampleDocuments(clearExisting = false): Promise<IngestResponse> {
  const response = await apiClient.post('/api/ingest/samples', null, {
    params: { clear_existing: clearExisting },
  })
  return response.data
}

/**
 * List available mock sample documents
 */
export async function listSampleDocuments(): Promise<{ documents: { title: string; text: string }[] }> {
  const response = await apiClient.get('/api/ingest/samples')
  return response.data
}

/**
 * List ingested documents (grouped by title) with chunk/entity counts
 */
export async function listDocuments(): Promise<{ documents: IngestedDocument[] }> {
  const response = await apiClient.get('/api/ingest/documents')
  return response.data
}

/**
 * Delete a single ingested document and the entities it uniquely added
 */
export async function deleteDocument(title: string): Promise<DeleteDocumentResponse> {
  const response = await apiClient.delete('/api/ingest/documents', {
    params: { title },
  })
  return response.data
}

/**
 * Get the status of the Knowledge Graph
 */
export async function getGraphStatus(): Promise<any> {
  const response = await apiClient.get('/api/ingest/status')
  return response.data
}

/**
 * Clear all data from the Knowledge Graph
 */
export async function clearGraph(): Promise<any> {
  const response = await apiClient.delete('/api/ingest/clear')
  return response.data
}

/**
 * Query the Knowledge Graph using the Librarian
 */
export async function queryLibrarian(request: LibrarianQueryRequest): Promise<LibrarianQueryResponse> {
  const response = await apiClient.post('/api/librarian/query', request)
  return response.data
}

/**
 * Stream a debate in real-time via POST + SSE
 */
export async function streamDebate(
  request: BoardroomDebateRequest,
  callbacks: BoardroomStreamCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_URL}/api/boardroom/debate/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    signal,
  })

  if (!response.ok) {
    let detail = `Debate stream failed (${response.status})`
    try {
      const body = await response.json()
      detail = body.detail || detail
    } catch {
      // ignore parse errors
    }
    callbacks.onError(detail)
    return
  }

  if (!response.body) {
    callbacks.onError('No response stream from server')
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        const event: BoardroomStreamEvent = JSON.parse(line.slice(6))
        if (event.error) {
          callbacks.onError(event.error)
          return
        }
        if (event.type === 'message' && event.agent && event.message && event.timestamp) {
          callbacks.onMessage({
            agent: event.agent,
            message: event.message,
            timestamp: event.timestamp,
            round_count: event.round_count,
          })
        }
        if (event.type === 'complete') {
          callbacks.onComplete({
            final_verdict: event.final_verdict || '',
            data_sources: event.data_sources || [],
          })
        }
      } catch {
        // skip malformed SSE chunks
      }
    }
  }
}

/**
 * Get graph data for visualization
 */
export async function getGraphData(limit = 150): Promise<GraphVisualizationResponse> {
  const response = await apiClient.get('/api/ingest/graph', { params: { limit } })
  return response.data
}

/**
 * Check API health
 */
export async function checkHealth(): Promise<any> {
  const response = await apiClient.get('/health')
  return response.data
}

// Made with Bob
