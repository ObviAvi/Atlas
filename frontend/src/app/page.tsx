'use client'

import { useState } from 'react'
import GraphExplorerTab from '@/components/GraphExplorerTab'
import LibrarianTab from '@/components/LibrarianTab'
import BoardroomTab from '@/components/BoardroomTab'
import { ArrowRight, BookOpen, Users, Network } from 'lucide-react'

type Tab = 'atlas' | 'librarian' | 'boardroom'

const TABS: { id: Tab; label: string; icon: typeof Network }[] = [
  { id: 'atlas', label: 'Atlas', icon: Network },
  { id: 'librarian', label: 'Librarian', icon: BookOpen },
  { id: 'boardroom', label: 'Boardroom', icon: Users },
]

export default function Home() {
  const [entered, setEntered] = useState(false)
  const [heroExiting, setHeroExiting] = useState(false)
  const [showHero, setShowHero] = useState(true)
  const [activeTab, setActiveTab] = useState<Tab>('atlas')

  const enter = () => {
    setEntered(true)
    setHeroExiting(true)
    window.setTimeout(() => setShowHero(false), 700)
  }

  return (
    <main className="fixed inset-0 overflow-hidden">
      {/* Persistent 3D knowledge graph — the backdrop for the entire app */}
      <GraphExplorerTab active={entered && activeTab === 'atlas'} />

      {/* Landing hero — opaque so it hides the graph, then fades out on enter */}
      {showHero && (
        <div
          className={`fixed inset-0 z-40 flex flex-col items-center justify-center px-6 text-center transition-opacity duration-700 ease-in ${
            heroExiting ? 'pointer-events-none opacity-0' : 'opacity-100 animate-fade-in'
          }`}
          style={{
            background: 'radial-gradient(circle at 50% 42%, #241a12 0%, #1a1612 48%, #100b08 100%)',
          }}
        >
          <div>
            <div className="mb-7 flex justify-center gap-2">
              <span className="pill-tag">GraphRAG</span>
              <span className="pill-tag">Multi-Agent</span>
            </div>
            <h1 className="font-display text-[clamp(4rem,16vw,11rem)] leading-none tracking-[0.04em] text-cream">
              Atlas
            </h1>
            <p className="mx-auto mt-7 max-w-xl text-sm leading-relaxed text-cream/70 md:text-base">
              Structure company data into a living knowledge graph. Query facts with the Librarian
              or stress-test new ideas in the Boardroom — all grounded in your company&rsquo;s own data.
            </p>
            <button
              onClick={enter}
              className="mt-10 inline-flex items-center gap-2 rounded-full bg-cream px-8 py-3.5 text-sm font-medium uppercase tracking-[0.14em] text-walnut-900 shadow-float transition-all duration-300 hover:gap-3 hover:bg-white"
            >
              Enter Atlas
              <ArrowRight size={18} />
            </button>
          </div>
        </div>
      )}

      {/* Librarian & Boardroom render as large, solid pages over the (dimmed) graph */}
      {entered && activeTab === 'librarian' && (
        <div className="fixed inset-0 z-30 overflow-y-auto bg-walnut-900/60 backdrop-blur-md">
          <div className="flex min-h-full justify-center px-4 pb-10 pt-24">
            <div className="min-h-[calc(100vh-8rem)] w-full max-w-5xl rounded-3xl border border-white/50 bg-cream p-6 shadow-float animate-fade-in md:p-10">
              <LibrarianTab />
            </div>
          </div>
        </div>
      )}

      {entered && activeTab === 'boardroom' && (
        <div className="fixed inset-0 z-30 overflow-y-auto bg-walnut-900/60 backdrop-blur-md">
          <div className="flex min-h-full justify-center px-4 pb-10 pt-24">
            <div className="min-h-[calc(100vh-8rem)] w-full max-w-6xl rounded-3xl border border-white/50 bg-cream p-6 shadow-float animate-fade-in md:p-10">
              <BoardroomTab />
            </div>
          </div>
        </div>
      )}

      {/* Floating navigation — appears once the user has entered */}
      {entered && (
        <nav className="fixed left-1/2 top-5 z-40 flex -translate-x-1/2 animate-fade-in items-center gap-1 rounded-full border border-white/10 bg-walnut-900/50 p-2 backdrop-blur-md">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-2 rounded-full px-4 py-2 text-xs font-medium uppercase tracking-[0.12em] transition-all duration-300 ${
                activeTab === id
                  ? 'bg-cream text-walnut-900 shadow-card'
                  : 'text-cream/60 hover:bg-white/10 hover:text-cream'
              }`}
            >
              <Icon size={14} />
              {label}
            </button>
          ))}
        </nav>
      )}
    </main>
  )
}

// Made with Bob
