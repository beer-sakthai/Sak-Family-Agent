import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from './App'
import { DEMO_DATA } from './data/demo-data'

const LIVE_DATA = {
  ...DEMO_DATA,
  source: 'live',
  generated_at: '2026-07-01',
  kpis: { ...DEMO_DATA.kpis, total_facts: 999 },
}

const originalFetch = global.fetch

function mockFetchOnce(response) {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => response,
  })
}

function mockFetchFailure() {
  global.fetch = vi.fn().mockRejectedValue(new Error('not found'))
}

describe('App', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    global.fetch = originalFetch
  })

  it('falls back to demo data and shows "Demo Mode" when data.json is unreachable', async () => {
    mockFetchFailure()
    render(<App />)

    expect(await screen.findByText('Demo Mode')).toBeInTheDocument()
    expect(screen.getByText(String(DEMO_DATA.kpis.total_facts))).toBeInTheDocument()
  })

  it('falls back to demo data when the response is not ok', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, json: async () => ({}) })
    render(<App />)

    expect(await screen.findByText('Demo Mode')).toBeInTheDocument()
  })

  it('renders live data and shows "Live" badge when data.json loads successfully', async () => {
    mockFetchOnce(LIVE_DATA)
    render(<App />)

    expect(await screen.findByText('Live Data')).toBeInTheDocument()
    expect(screen.getByText('999')).toBeInTheDocument()
    expect(screen.getByText(/Snapshot from 2026-07-01/)).toBeInTheDocument()
  })

  it('defaults to the Overview tab and renders its KPI cards', async () => {
    mockFetchOnce(LIVE_DATA)
    render(<App />)

    await screen.findByText('Live Data')
    expect(screen.getByText('Total Facts')).toBeInTheDocument()
    expect(screen.getByText('Total Sessions')).toBeInTheDocument()
    expect(screen.getByText('Skills Library')).toBeInTheDocument()
  })

  it('switches tabs when a sidebar item is clicked', async () => {
    mockFetchOnce(LIVE_DATA)
    const user = userEvent.setup()
    render(<App />)

    await screen.findByText('Live Data')

    const nav = screen.getByRole('navigation')
    await user.click(within(nav).getByText('Skills'))

    expect(screen.getByRole('heading', { name: 'Skills' })).toBeInTheDocument()
    expect(screen.getByText(/skills across .* categories/)).toBeInTheDocument()
  })

  it('renders recent facts in the Memory tab', async () => {
    mockFetchOnce(LIVE_DATA)
    const user = userEvent.setup()
    render(<App />)

    await screen.findByText('Live Data')
    const nav = screen.getByRole('navigation')
    await user.click(within(nav).getByText('Memory'))

    for (const fact of LIVE_DATA.recent_facts) {
      expect(screen.getByText(fact.value)).toBeInTheDocument()
    }
  })

  it('shows an empty-state message in Agent Activity when there are no sessions', async () => {
    mockFetchOnce({ ...LIVE_DATA, recent_sessions: [] })
    const user = userEvent.setup()
    render(<App />)

    await screen.findByText('Live Data')
    const nav = screen.getByRole('navigation')
    await user.click(within(nav).getByText('Agent Activity'))

    expect(screen.getByText('No sessions recorded yet.')).toBeInTheDocument()
  })

  it('computes total_skills from the skills array when kpis.total_skills is absent', async () => {
    const dataWithoutKpiSkillCount = {
      ...LIVE_DATA,
      kpis: { ...LIVE_DATA.kpis, total_skills: undefined },
      skills: [{ category: 'coding', count: 3, skills: [] }],
    }
    mockFetchOnce(dataWithoutKpiSkillCount)
    render(<App />)

    await screen.findByText('Live Data')
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('renders thought process groups, messages, and confidence in Chat & Reasoning', async () => {
    mockFetchOnce(LIVE_DATA)
    const user = userEvent.setup()
    render(<App />)

    await screen.findByText('Live Data')
    const nav = screen.getByRole('navigation')
    await user.click(within(nav).getByText('Chat & Reasoning'))

    for (const group of LIVE_DATA.chat.thought_process) {
      expect(screen.getByText(group.group)).toBeInTheDocument()
      for (const step of group.steps) {
        expect(screen.getByText(step)).toBeInTheDocument()
      }
    }
    for (const msg of LIVE_DATA.chat.messages) {
      expect(screen.getByText(msg.text)).toBeInTheDocument()
    }
    expect(screen.getByText(`${LIVE_DATA.chat.confidence}%`)).toBeInTheDocument()
  })

  it('renders performance stats and version history in Evolution', async () => {
    mockFetchOnce(LIVE_DATA)
    const user = userEvent.setup()
    render(<App />)

    await screen.findByText('Live Data')
    const nav = screen.getByRole('navigation')
    await user.click(within(nav).getByText('Evolution'))

    expect(screen.getAllByText(LIVE_DATA.evolution.performance_gain).length).toBeGreaterThan(0)
    expect(screen.getByText(`${LIVE_DATA.evolution.success_rate}%`)).toBeInTheDocument()
    expect(screen.getByText('v2.2.0')).toBeInTheDocument()
    expect(screen.getByText('v2.0.0')).toBeInTheDocument()
  })

  it('renders the architecture layers and tool registry in Project', async () => {
    mockFetchOnce(LIVE_DATA)
    const user = userEvent.setup()
    render(<App />)

    await screen.findByText('Live Data')
    const nav = screen.getByRole('navigation')
    await user.click(within(nav).getByText('Project'))

    expect(screen.getByRole('heading', { name: 'SakThai-Agent' })).toBeInTheDocument()
    expect(screen.getByText('CLI / MCP')).toBeInTheDocument()
    expect(screen.getByText('MemoryStore')).toBeInTheDocument()
    expect(screen.getByText('learn')).toBeInTheDocument()
    expect(screen.getByText('Claude')).toBeInTheDocument()
    expect(screen.getByText('Dream')).toBeInTheDocument()
  })
})
