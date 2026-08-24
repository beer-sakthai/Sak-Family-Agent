import { describe, it, expect, vi, beforeEach } from 'vitest';
import { GET, POST } from '../app/api/recovery/route';
import { NextRequest } from 'next/server';
import { selfHealingDashboardEngine } from '@/lib/selfHealingEngine';

// We mock the engine to strictly control test boundaries, avoiding actual engine state manipulation.
vi.mock('@/lib/selfHealingEngine', () => ({
  selfHealingDashboardEngine: {
    getIncidents: vi.fn(),
    getPersonaHealth: vi.fn(),
    replayIncident: vi.fn(),
    resetCircuit: vi.fn(),
  }
}));

describe('Recovery API Route', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('GET /api/recovery returns incidents, health, and timestamp', async () => {
    const mockIncidents = [{ id: 'inc1' }];
    const mockHealth = [{ persona: 'SakSee', status: 'healthy' }];

    vi.mocked(selfHealingDashboardEngine.getIncidents).mockReturnValue(mockIncidents as any);
    vi.mocked(selfHealingDashboardEngine.getPersonaHealth).mockReturnValue(mockHealth as any);

    const req = new NextRequest('http://localhost:3000/api/recovery');
    const res = await GET(req);

    expect(res.status).toBe(200);
    const json = await res.json();

    expect(json.success).toBe(true);
    expect(json.data.incidents).toEqual(mockIncidents);
    expect(json.data.health).toEqual(mockHealth);
    expect(json.data.timestamp).toBeDefined();

    expect(selfHealingDashboardEngine.getIncidents).toHaveBeenCalledTimes(1);
    expect(selfHealingDashboardEngine.getPersonaHealth).toHaveBeenCalledTimes(1);
  });

  it('POST /api/recovery handles replay action successfully', async () => {
    const mockIncident = { id: 'inc1', status: 'replayed' };
    vi.mocked(selfHealingDashboardEngine.replayIncident).mockReturnValue({
      success: true,
      incident: mockIncident as any,
    });

    const req = new NextRequest('http://localhost:3000/api/recovery', {
      method: 'POST',
      body: JSON.stringify({ action: 'replay', id: 'inc1' })
    });
    const res = await POST(req);

    expect(res.status).toBe(200);
    const json = await res.json();

    expect(json.success).toBe(true);
    expect(json.incident).toEqual(mockIncident);
    expect(selfHealingDashboardEngine.replayIncident).toHaveBeenCalledWith('inc1');
  });

  it('POST /api/recovery handles replay action failure', async () => {
    vi.mocked(selfHealingDashboardEngine.replayIncident).mockReturnValue({
      success: false,
    });

    const req = new NextRequest('http://localhost:3000/api/recovery', {
      method: 'POST',
      body: JSON.stringify({ action: 'replay', id: 'inc1' })
    });
    const res = await POST(req);

    expect(res.status).toBe(200); // 200 because the action executed, but the result is failure
    const json = await res.json();

    expect(json.success).toBe(false);
    expect(selfHealingDashboardEngine.replayIncident).toHaveBeenCalledWith('inc1');
  });

  it('POST /api/recovery handles reset_circuit action', async () => {
    vi.mocked(selfHealingDashboardEngine.resetCircuit).mockReturnValue(true);

    const req = new NextRequest('http://localhost:3000/api/recovery', {
      method: 'POST',
      body: JSON.stringify({ action: 'reset_circuit', persona: 'SakKing' })
    });
    const res = await POST(req);

    expect(res.status).toBe(200);
    const json = await res.json();

    expect(json.success).toBe(true);
    expect(selfHealingDashboardEngine.resetCircuit).toHaveBeenCalledWith('SakKing');
  });

  it('POST /api/recovery handles reset_circuit action failure', async () => {
    vi.mocked(selfHealingDashboardEngine.resetCircuit).mockReturnValue(false);

    const req = new NextRequest('http://localhost:3000/api/recovery', {
      method: 'POST',
      body: JSON.stringify({ action: 'reset_circuit', persona: 'SakUnknown' })
    });
    const res = await POST(req);

    expect(res.status).toBe(200);
    const json = await res.json();

    expect(json.success).toBe(false); // Map success from the handler logic
    expect(selfHealingDashboardEngine.resetCircuit).toHaveBeenCalledWith('SakUnknown');
  });

  it('POST /api/recovery rejects invalid action', async () => {
    const req = new NextRequest('http://localhost:3000/api/recovery', {
      method: 'POST',
      body: JSON.stringify({ action: 'invalid_action' })
    });
    const res = await POST(req);

    expect(res.status).toBe(500); // Maps to 500 in createMutationHandler
    const json = await res.json();

    expect(json.success).toBe(false);
    expect(json.error).toContain('Invalid recovery action or missing arguments');
  });

  it('POST /api/recovery rejects missing arguments', async () => {
    // Action 'replay' but missing 'id'
    const req1 = new NextRequest('http://localhost:3000/api/recovery', {
      method: 'POST',
      body: JSON.stringify({ action: 'replay' }) // missing id
    });
    const res1 = await POST(req1);
    expect(res1.status).toBe(500);
    const json1 = await res1.json();
    expect(json1.success).toBe(false);
    expect(json1.error).toContain('Invalid recovery action or missing arguments');

    // Action 'reset_circuit' but missing 'persona'
    const req2 = new NextRequest('http://localhost:3000/api/recovery', {
      method: 'POST',
      body: JSON.stringify({ action: 'reset_circuit' }) // missing persona
    });
    const res2 = await POST(req2);
    expect(res2.status).toBe(500);
    const json2 = await res2.json();
    expect(json2.success).toBe(false);
    expect(json2.error).toContain('Invalid recovery action or missing arguments');
  });
});
