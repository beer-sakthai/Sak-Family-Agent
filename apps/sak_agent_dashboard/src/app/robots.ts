import type { MetadataRoute } from "next";

/**
 * Disallow everything.
 *
 * The page metadata already carries `noindex, nofollow`, but that is only read
 * once a crawler has fetched the page. This stops the fetch, and covers the
 * `/api/*` routes, which have no HTML head to carry a robots tag at all — and
 * which, on a deploy pointed at a live agent, serve real session transcripts.
 */
export default function robots(): MetadataRoute.Robots {
  return {
    rules: [{ userAgent: "*", disallow: "/" }],
  };
}
