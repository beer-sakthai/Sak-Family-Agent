import { NextRequest, NextResponse } from 'next/server';
import { ServiceRegistry } from '@/lib/a2a/serviceRegistry';
import { A2AEngine } from '@/lib/a2a/a2aEngine';
import { A2ADelegationRequest } from '@/lib/a2a/types';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const action = searchParams.get('action') || 'all';

    if (action === 'fleet') {
      const fleet = ServiceRegistry.getAllAgents();
      return NextResponse.json({ success: true, fleet });
    }

    if (action === 'health') {
      const health = ServiceRegistry.getFleetHealth();
      return NextResponse.json({ success: true, health });
    }

    if (action === 'delegations') {
      const delegations = A2AEngine.getRecentDelegations();
      return NextResponse.json({ success: true, delegations });
    }

    const fleet = ServiceRegistry.getAllAgents();
    const health = ServiceRegistry.getFleetHealth();
    const delegations = A2AEngine.getRecentDelegations();

    return NextResponse.json({
      success: true,
      data: {
        fleet,
        health,
        delegations
      }
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown A2A registry error';
    return NextResponse.json({ success: false, error: message }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action } = body;

    if (action === 'delegate') {
      const req: A2ADelegationRequest = {
        agentFrom: body.agentFrom || 'sakking',
        agentTo: body.agentTo,
        capabilityId: body.capabilityId,
        payload: body.payload || {},
        timeoutMs: body.timeoutMs || 5000
      };

      if (!req.agentTo || !req.capabilityId) {
        return NextResponse.json(
          { success: false, error: 'agentTo and capabilityId are required' },
          { status: 400 }
        );
      }

      const result = await A2AEngine.delegateTask(req);
      return NextResponse.json({ success: true, result });
    }

    if (action === 'heartbeat') {
      const { agentSlug } = body;
      if (!agentSlug) {
        return NextResponse.json({ success: false, error: 'agentSlug is required' }, { status: 400 });
      }

      const recorded = ServiceRegistry.recordHeartbeat(agentSlug);
      return NextResponse.json({ success: recorded });
    }

    if (action === 'discover') {
      const { category } = body;
      const capabilities = ServiceRegistry.discoverCapabilities(category);
      return NextResponse.json({ success: true, capabilities });
    }

    return NextResponse.json({ success: false, error: `Invalid action: ${action}` }, { status: 400 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown A2A registry error';
    return NextResponse.json({ success: false, error: message }, { status: 500 });
  }
}
