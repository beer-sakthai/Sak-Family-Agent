import { NextResponse } from "next/server";

/**
 * Route-handler factory (Template Method).
 *
 * Every read-only API route in this dashboard used to hand-roll the same
 * envelope: parse `?demo=`, call a data module, wrap the result in
 * `{ success: true, ...data }`, and on failure log a `Secure Log` line and
 * return a 500 `{ success: false, error }`. That boilerplate was duplicated
 * across ~45 GET routes. `createApiHandler` is the template: it owns the
 * try/catch, the demo-param parsing, the success envelope, and the error
 * envelope, while the per-route `handler` supplies only the data it produces.
 */

/** Custom API Error class supporting status codes and structured details. */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Everything a route handler needs, parsed once from the incoming request. */
export interface ApiContext {
  request: Request;
  /** `true` when the request carries `?demo=true`. */
  demo: boolean;
  /** All query parameters, keyed by name (last value wins on duplicates). */
  params: Record<string, string | undefined>;
}

/** The `Secure Log` prefix shared by every route's error logging. */
export const SECURE_LOG_PREFIX = "Secure Log";

/** Parse the demo flag and query params out of a request exactly once. */
export function buildContext(request?: Request): ApiContext {
  const url = new URL(request?.url ?? "http://localhost:3000");
  const params: Record<string, string | undefined> = {};
  url.searchParams.forEach((value, key) => {
    params[key] = value;
  });
  return {
    request: request ?? new Request(url.toString()),
    demo: url.searchParams.get("demo") === "true",
    params,
  };
}

/**
 * Build a `GET` route handler from a data-producing function.
 */
export function createApiHandler<T extends Record<string, unknown>>(
  label: string,
  handler: (ctx: ApiContext) => Promise<T>,
): (request?: Request) => Promise<Response> {
  return async (request) => {
    try {
      const data = await handler(buildContext(request));
      const { _status = 200, ...rest } = data as { _status?: number };
      return NextResponse.json({ success: true, ...rest }, { status: _status });
    } catch (error) {
      if (error instanceof ApiError) {
        return NextResponse.json(
          {
            success: false,
            error: error.message,
            ...(error.details !== undefined ? { details: error.details } : {}),
          },
          { status: error.status },
        );
      }
      console.error(`${SECURE_LOG_PREFIX} [GET ${label}]:`, error);
      const msg = error instanceof Error ? error.message : `An unexpected error occurred while ${label}.`;
      return NextResponse.json(
        { success: false, error: msg },
        { status: 500 },
      );
    }
  };
}

/**
 * Build a `POST` route handler from a body-consuming function.
 */
export function createMutationHandler<T extends Record<string, unknown>>(
  label: string,
  handler: (body: Record<string, unknown>, ctx: ApiContext) => Promise<T>,
): (request: Request) => Promise<Response> {
  return async (request) => {
    try {
      const ctx = buildContext(request);
      let body: Record<string, unknown> = {};
      try {
        body = (await request.json()) as Record<string, unknown>;
      } catch {
        // A missing or malformed body is not fatal; the handler decides.
      }
      const data = await handler(body, ctx);
      const { _status = 200, ...rest } = data as { _status?: number };
      return NextResponse.json({ success: true, ...rest }, { status: _status });
    } catch (error) {
      if (error instanceof ApiError) {
        return NextResponse.json(
          {
            success: false,
            error: error.message,
            ...(error.details !== undefined ? { details: error.details } : {}),
          },
          { status: error.status },
        );
      }
      console.error(`${SECURE_LOG_PREFIX} [POST ${label}]:`, error);
      const msg = error instanceof Error ? error.message : `An unexpected error occurred while ${label}.`;
      return NextResponse.json(
        { success: false, error: msg },
        { status: 500 },
      );
    }
  };
}
