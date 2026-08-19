import { NextRequest, NextResponse } from 'next/server';
import { SemanticCacheEngine } from '@/lib/cache/semanticCacheEngine';
import { CacheLookupQuery } from '@/lib/cache/types';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const action = searchParams.get('action') || 'all';

    if (action === 'analytics') {
      const analytics = SemanticCacheEngine.getAnalytics();
      return NextResponse.json({ success: true, analytics });
    }

    if (action === 'entries') {
      const entries = SemanticCacheEngine.getAllEntries();
      return NextResponse.json({ success: true, entries });
    }

    const analytics = SemanticCacheEngine.getAnalytics();
    const entries = SemanticCacheEngine.getAllEntries();

    return NextResponse.json({
      success: true,
      data: {
        analytics,
        entries
      }
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown cache error';
    return NextResponse.json({ success: false, error: message }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action } = body;

    if (action === 'lookup') {
      const query: CacheLookupQuery = {
        prompt: body.prompt || '',
        personaSlug: body.personaSlug,
        model: body.model,
        minSimilarity: body.minSimilarity ? parseFloat(body.minSimilarity) : undefined
      };

      if (!query.prompt.trim()) {
        return NextResponse.json({ success: false, error: 'prompt is required' }, { status: 400 });
      }

      const result = SemanticCacheEngine.lookup(query);
      return NextResponse.json({ success: true, result });
    }

    if (action === 'store') {
      const { prompt, response, personaSlug, model, ttlSeconds, similarityThreshold } = body;
      if (!prompt || !response) {
        return NextResponse.json(
          { success: false, error: 'prompt and response are required' },
          { status: 400 }
        );
      }

      const entry = SemanticCacheEngine.store(
        prompt,
        response,
        personaSlug,
        model,
        ttlSeconds,
        similarityThreshold
      );
      return NextResponse.json({ success: true, entry });
    }

    if (action === 'invalidate') {
      const { id, personaSlug } = body;
      const count = SemanticCacheEngine.invalidate(id, personaSlug);
      return NextResponse.json({ success: true, deletedCount: count });
    }

    if (action === 'clear') {
      const count = SemanticCacheEngine.invalidate();
      return NextResponse.json({ success: true, deletedCount: count });
    }

    return NextResponse.json({ success: false, error: `Invalid action: ${action}` }, { status: 400 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown cache error';
    return NextResponse.json({ success: false, error: message }, { status: 500 });
  }
}
