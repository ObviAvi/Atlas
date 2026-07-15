'use client'

import { Brain, Database, Scale, ShieldAlert, TrendingUp } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

type AgentSide = 'left' | 'right' | 'center'

const AGENT_CONFIG: Record<
  string,
  { side: AgentSide; icon: typeof Brain; accent: string; ring: string; bubble: string }
> = {
  Supervisor: {
    side: 'center',
    icon: Brain,
    accent: 'text-walnut-700',
    ring: 'ring-walnut-400/40',
    bubble: 'border-walnut-300/40 bg-sand-100/90',
  },
  Retrieval: {
    side: 'center',
    icon: Database,
    accent: 'text-walnut-600',
    ring: 'ring-sand-400/50',
    bubble: 'border-sand-300/60 bg-cream/95',
  },
  Strategist: {
    side: 'left',
    icon: TrendingUp,
    accent: 'text-emerald-800',
    ring: 'ring-emerald-400/50',
    bubble: 'border-emerald-200/70 bg-emerald-50/80',
  },
  'Risk Analyst': {
    side: 'right',
    icon: ShieldAlert,
    accent: 'text-rose-800',
    ring: 'ring-rose-400/50',
    bubble: 'border-rose-200/70 bg-rose-50/80',
  },
  Synthesizer: {
    side: 'center',
    icon: Scale,
    accent: 'text-amber-900',
    ring: 'ring-amber-400/50',
    bubble: 'border-amber-200/70 bg-amber-50/80',
  },
}

function AgentAvatar({
  agent,
  isActive,
  isThinking,
}: {
  agent: string
  isActive: boolean
  isThinking: boolean
}) {
  const config = AGENT_CONFIG[agent]
  if (!config) return null
  const Icon = config.icon

  return (
    <div
      className={`flex flex-col items-center gap-2 transition-all duration-500 ${
        isActive ? 'scale-105' : isThinking ? 'scale-100 opacity-100' : 'scale-95 opacity-60'
      }`}
    >
      <div
        className={`relative flex h-16 w-16 md:h-20 md:w-20 items-center justify-center rounded-full border-2 bg-white/80 shadow-card transition-all duration-500 ${
          isActive
            ? `border-walnut-700/20 ring-4 ${config.ring} animate-debate-pulse`
            : isThinking
              ? `border-walnut-700/15 ring-2 ${config.ring} animate-debate-bounce`
              : 'border-walnut-700/10'
        }`}
      >
        <Icon className={`${config.accent}`} size={28} />
        {isThinking && (
          <span className="absolute -bottom-1 flex gap-1 rounded-full bg-walnut-900 px-2 py-0.5">
            <span className="h-1 w-1 rounded-full bg-cream animate-bounce [animation-delay:0ms]" />
            <span className="h-1 w-1 rounded-full bg-cream animate-bounce [animation-delay:150ms]" />
            <span className="h-1 w-1 rounded-full bg-cream animate-bounce [animation-delay:300ms]" />
          </span>
        )}
      </div>
      <span className="text-[10px] uppercase tracking-[0.14em] text-walnut-500 font-medium">
        {agent}
      </span>
    </div>
  )
}

function TypingDots() {
  return (
    <div className="flex items-center gap-1.5 py-2">
      <span className="h-2 w-2 rounded-full bg-walnut-400 animate-bounce [animation-delay:0ms]" />
      <span className="h-2 w-2 rounded-full bg-walnut-400 animate-bounce [animation-delay:120ms]" />
      <span className="h-2 w-2 rounded-full bg-walnut-400 animate-bounce [animation-delay:240ms]" />
    </div>
  )
}

interface DebateArenaProps {
  activeAgent: string | null
  thinkingAgent: string | null
  speechAgent: string | null
  speechText: string
  isStreamingSpeech: boolean
  idea: string
}

export default function DebateArena({
  activeAgent,
  thinkingAgent,
  speechAgent,
  speechText,
  isStreamingSpeech,
  idea,
}: DebateArenaProps) {
  const speechSide = speechAgent ? AGENT_CONFIG[speechAgent]?.side ?? 'center' : 'center'
  const speechConfig = speechAgent ? AGENT_CONFIG[speechAgent] : null

  const bubbleAlign =
    speechSide === 'left'
      ? 'mr-auto max-w-[85%] animate-debate-slide-left'
      : speechSide === 'right'
        ? 'ml-auto max-w-[85%] animate-debate-slide-right'
        : 'mx-auto max-w-[90%] animate-fade-in'

  return (
    <div className="surface-card overflow-hidden">
      <div className="border-b border-walnut-700/10 bg-gradient-to-r from-sand-100/80 via-cream to-sand-100/80 px-5 py-4">
        <p className="text-[11px] uppercase tracking-[0.14em] text-walnut-500 mb-1">Live debate</p>
        <p className="font-display text-lg text-walnut-900 line-clamp-2">&ldquo;{idea}&rdquo;</p>
      </div>

      <div className="relative px-4 py-8 md:px-8 md:py-10">
        {/* Center support agents */}
        <div className="flex justify-center gap-8 md:gap-14 mb-8">
          {['Supervisor', 'Retrieval'].map((agent) => (
            <AgentAvatar
              key={agent}
              agent={agent}
              isActive={activeAgent === agent}
              isThinking={thinkingAgent === agent}
            />
          ))}
        </div>

        {/* Main debate line */}
        <div className="relative grid grid-cols-[1fr_auto_1fr] items-end gap-3 md:gap-6 min-h-[120px]">
          <div className="flex justify-center md:justify-end">
            <AgentAvatar
              agent="Strategist"
              isActive={activeAgent === 'Strategist'}
              isThinking={thinkingAgent === 'Strategist'}
            />
          </div>

          <div className="hidden md:block w-px h-16 bg-gradient-to-b from-transparent via-walnut-700/15 to-transparent" />

          <div className="flex justify-center md:justify-start">
            <AgentAvatar
              agent="Risk Analyst"
              isActive={activeAgent === 'Risk Analyst'}
              isThinking={thinkingAgent === 'Risk Analyst'}
            />
          </div>
        </div>

        {/* Animated connector when debating */}
        {(activeAgent === 'Strategist' || activeAgent === 'Risk Analyst') && (
          <div className="absolute left-1/2 top-[52%] -translate-x-1/2 -translate-y-1/2 hidden md:flex items-center gap-2 pointer-events-none">
            <span
              className={`h-0.5 w-12 rounded-full transition-all duration-700 ${
                activeAgent === 'Strategist' ? 'bg-emerald-400/60 w-20' : 'bg-walnut-300/30 w-12'
              }`}
            />
            <span className="text-[10px] uppercase tracking-widest text-walnut-400">vs</span>
            <span
              className={`h-0.5 w-12 rounded-full transition-all duration-700 ${
                activeAgent === 'Risk Analyst' ? 'bg-rose-400/60 w-20' : 'bg-walnut-300/30 w-12'
              }`}
            />
          </div>
        )}

        {/* Speech bubble */}
        <div className="mt-8 min-h-[100px]">
          {speechAgent && (speechText || isStreamingSpeech) ? (
            <div className={`rounded-2xl border p-5 md:p-6 ${bubbleAlign} ${speechConfig?.bubble ?? ''}`}>
              <p className="text-[10px] uppercase tracking-[0.14em] text-walnut-500 mb-2">
                {speechAgent}
              </p>
              <div className="text-sm text-walnut-700 leading-relaxed [&_p]:mb-2 [&_strong]:text-walnut-900">
                {speechText ? (
                  <ReactMarkdown>{speechText}</ReactMarkdown>
                ) : (
                  <TypingDots />
                )}
                {isStreamingSpeech && speechText && (
                  <span className="inline-block w-0.5 h-4 ml-0.5 bg-walnut-600 animate-pulse align-middle" />
                )}
              </div>
            </div>
          ) : thinkingAgent ? (
            <div className="mx-auto max-w-md rounded-2xl border border-walnut-700/10 bg-white/50 p-5 text-center animate-fade-in">
              <p className="text-xs uppercase tracking-[0.14em] text-walnut-500 mb-2">
                {thinkingAgent} is preparing
              </p>
              <TypingDots />
            </div>
          ) : null}
        </div>

        {/* Synthesizer slot */}
        <div className="mt-8 flex justify-center">
          <AgentAvatar
            agent="Synthesizer"
            isActive={activeAgent === 'Synthesizer'}
            isThinking={thinkingAgent === 'Synthesizer'}
          />
        </div>
      </div>
    </div>
  )
}

// Made with Bob
