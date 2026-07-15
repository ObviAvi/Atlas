'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { streamDebate, AgentMessage } from '@/lib/api'
import { Send, Loader2, Users, CheckCircle2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import DebateArena from '@/components/DebateArena'

const TYPEWRITER_CHUNK = 14
const TYPEWRITER_DELAY_MS = 22

function getNextAgent(lastAgent: string, roundCount: number, maxRounds: number): string | null {
  switch (lastAgent) {
    case 'Supervisor':
      return 'Retrieval'
    case 'Retrieval':
      return 'Strategist'
    case 'Strategist':
      return 'Risk Analyst'
    case 'Risk Analyst':
      return roundCount >= maxRounds ? 'Synthesizer' : 'Strategist'
    default:
      return null
  }
}

function getAgentStyle(agent: string) {
  switch (agent) {
    case 'Supervisor':
      return 'border-walnut-300/40 bg-sand-100/80'
    case 'Retrieval':
      return 'border-sand-300/60 bg-cream/90'
    case 'Strategist':
      return 'border-emerald-200/60 bg-emerald-50/50'
    case 'Risk Analyst':
      return 'border-rose-200/60 bg-rose-50/50'
    case 'Synthesizer':
      return 'border-amber-200/60 bg-amber-50/50'
    default:
      return 'border-walnut-700/10 bg-white/60'
  }
}

export default function BoardroomTab() {
  const [idea, setIdea] = useState('')
  const [rounds, setRounds] = useState(3)
  const [debating, setDebating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [submittedIdea, setSubmittedIdea] = useState('')
  const [transcript, setTranscript] = useState<AgentMessage[]>([])
  const [activeAgent, setActiveAgent] = useState<string | null>(null)
  const [thinkingAgent, setThinkingAgent] = useState<string | null>(null)
  const [speechAgent, setSpeechAgent] = useState<string | null>(null)
  const [speechText, setSpeechText] = useState('')
  const [isStreamingSpeech, setIsStreamingSpeech] = useState(false)
  const [finalVerdict, setFinalVerdict] = useState('')
  const [dataSources, setDataSources] = useState<string[]>([])
  const [isComplete, setIsComplete] = useState(false)

  const abortRef = useRef<AbortController | null>(null)
  const messageQueueRef = useRef<Array<AgentMessage & { round_count?: number }>>([])
  const processingRef = useRef(false)
  const roundsRef = useRef(rounds)

  useEffect(() => {
    roundsRef.current = rounds
  }, [rounds])

  const typewriterReveal = useCallback(async (fullText: string, signal: AbortSignal) => {
    setSpeechText('')
    for (let i = 0; i <= fullText.length; i += TYPEWRITER_CHUNK) {
      if (signal.aborted) return
      setSpeechText(fullText.slice(0, i))
      await new Promise((resolve) => setTimeout(resolve, TYPEWRITER_DELAY_MS))
    }
    setSpeechText(fullText)
  }, [])

  const processMessageQueue = useCallback(async () => {
    if (processingRef.current) return
    processingRef.current = true

    while (messageQueueRef.current.length > 0) {
      const msg = messageQueueRef.current.shift()!
      setActiveAgent(msg.agent)
      setThinkingAgent(null)
      setSpeechAgent(msg.agent)
      setIsStreamingSpeech(true)

      const localSignal = abortRef.current?.signal ?? new AbortController().signal
      await typewriterReveal(msg.message, localSignal)

      if (localSignal.aborted) break

      setIsStreamingSpeech(false)
      setTranscript((prev) => [...prev, { agent: msg.agent, message: msg.message, timestamp: msg.timestamp }])

      if (msg.agent === 'Synthesizer') {
        setFinalVerdict(msg.message)
      }

      const next = getNextAgent(msg.agent, msg.round_count ?? 0, roundsRef.current)
      setThinkingAgent(next)
      setSpeechAgent(null)
      setSpeechText('')

      await new Promise((resolve) => setTimeout(resolve, 400))
    }

    processingRef.current = false
  }, [typewriterReveal])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!idea.trim() || debating) return

    abortRef.current?.abort()
    abortRef.current = new AbortController()

    setDebating(true)
    setError(null)
    setTranscript([])
    setFinalVerdict('')
    setDataSources([])
    setIsComplete(false)
    setActiveAgent(null)
    setSpeechAgent(null)
    setSpeechText('')
    setSubmittedIdea(idea.trim())
    setThinkingAgent('Supervisor')
    messageQueueRef.current = []
    processingRef.current = false

    try {
      await streamDebate(
        { idea: idea.trim(), rounds },
        {
          onMessage: (msg) => {
            messageQueueRef.current.push(msg)
            void processMessageQueue()
          },
          onComplete: (result) => {
            const waitForQueue = async () => {
              while (processingRef.current || messageQueueRef.current.length > 0) {
                await new Promise((resolve) => setTimeout(resolve, 100))
              }
              setThinkingAgent(null)
              setActiveAgent('Synthesizer')
              setDataSources(result.data_sources)
              if (result.final_verdict) {
                setFinalVerdict((prev) => prev || result.final_verdict)
              }
              setIsComplete(true)
              setDebating(false)
            }
            void waitForQueue()
          },
          onError: (err) => {
            setError(err)
            setDebating(false)
            setThinkingAgent(null)
          },
        },
        abortRef.current.signal,
      )
    } catch (err: any) {
      if (err?.name !== 'AbortError') {
        setError(err?.message || 'Failed to start debate')
      }
      setDebating(false)
      setThinkingAgent(null)
    }
  }

  useEffect(() => {
    return () => abortRef.current?.abort()
  }, [])

  const showArena = debating || transcript.length > 0 || isComplete

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="font-display text-3xl md:text-4xl text-walnut-900">The Boardroom</h2>
          <p className="mt-2 text-sm text-walnut-600 max-w-xl">
            Propose an idea and watch agents debate it live. The Strategist argues for, the Risk
            Analyst argues against, and the Synthesizer delivers a grounded executive verdict.
          </p>
        </div>
        <Users className="text-walnut-400 hidden md:block" size={36} />
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="idea" className="block text-[11px] uppercase tracking-[0.14em] text-walnut-500 mb-2">
            Your idea
          </label>
          <textarea
            id="idea"
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
            placeholder="We should allocate more budget to Project Alpha to accelerate delivery"
            className="input-field"
            rows={3}
            disabled={debating}
          />
        </div>

        <div>
          <label htmlFor="rounds" className="block text-[11px] uppercase tracking-[0.14em] text-walnut-500 mb-2">
            Debate rounds — {rounds}
          </label>
          <input
            type="range"
            id="rounds"
            min="1"
            max="5"
            value={rounds}
            onChange={(e) => setRounds(parseInt(e.target.value))}
            className="w-full accent-walnut-800"
            disabled={debating}
          />
          <div className="flex justify-between text-xs text-walnut-400 mt-1 uppercase tracking-wider">
            <span>Quick</span>
            <span>Thorough</span>
          </div>
        </div>

        <button type="submit" disabled={debating || !idea.trim()} className="btn-primary w-full md:w-auto">
          {debating ? (
            <>
              <Loader2 className="animate-spin" size={18} />
              Debate in progress…
            </>
          ) : (
            <>
              <Send size={18} />
              Start Debate
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

      {showArena && (
        <div className="space-y-6 animate-fade-in">
          <DebateArena
            activeAgent={activeAgent}
            thinkingAgent={thinkingAgent}
            speechAgent={speechAgent}
            speechText={speechText}
            isStreamingSpeech={isStreamingSpeech}
            idea={submittedIdea}
          />

          {transcript.length > 0 && (
            <details className="surface-card p-5 group" open={isComplete}>
              <summary className="cursor-pointer text-[11px] uppercase tracking-[0.14em] text-walnut-500 list-none flex items-center justify-between">
                Full transcript
                <span className="text-walnut-400 normal-case tracking-normal text-xs">
                  {transcript.length} messages
                </span>
              </summary>
              <div className="mt-4 space-y-3 max-h-[420px] overflow-y-auto pr-1">
                {transcript.map((msg, index) => (
                  <div key={index} className={`rounded-xl border p-4 ${getAgentStyle(msg.agent)}`}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-display text-base text-walnut-900">{msg.agent}</span>
                      <span className="text-[10px] uppercase tracking-wider text-walnut-400">
                        {new Date(msg.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="text-sm text-walnut-700 leading-relaxed [&_p]:mb-2">
                      <ReactMarkdown>{msg.message}</ReactMarkdown>
                    </div>
                  </div>
                ))}
              </div>
            </details>
          )}

          {isComplete && finalVerdict && (
            <div className="rounded-3xl border-2 border-walnut-700/15 bg-gradient-to-br from-cream to-sand-100 p-6 md:p-8 animate-fade-up">
              <div className="flex items-center gap-2 mb-4">
                <CheckCircle2 className="text-walnut-700" size={22} />
                <p className="font-display text-2xl text-walnut-900">Final Verdict</p>
              </div>
              <div className="text-walnut-700 leading-relaxed [&_p]:mb-3 [&_strong]:text-walnut-900">
                <ReactMarkdown>{finalVerdict}</ReactMarkdown>
              </div>
            </div>
          )}

          {isComplete && dataSources.length > 0 && (
            <div className="rounded-2xl border border-walnut-700/10 bg-sand-100/50 p-6">
              <p className="text-[11px] uppercase tracking-[0.14em] text-walnut-500 mb-3">Data sources</p>
              <div className="space-y-2">
                {dataSources.map((source, index) => (
                  <div key={index} className="rounded-xl bg-white/70 p-3 border border-walnut-700/5">
                    <p className="text-sm text-walnut-600 line-clamp-3">{source}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// Made with Bob
