import { NextRequest, NextResponse } from "next/server";
import { getDocBySlug } from "@/lib/docs";

export async function GET(
  _request: NextRequest,
  props: { params: Promise<{ page: string }> | { page: string } }
) {
  try {
    const params = await Promise.resolve(props.params);
    const { page } = params;

    if (!page) {
      return NextResponse.json(
        { success: false, error: "Missing document slug" },
        { status: 400 }
      );
    }

    const doc = getDocBySlug(page);
    if (!doc) {
      return NextResponse.json(
        { success: false, error: `Document '${page}' not found` },
        { status: 404 }
      );
    }

    return NextResponse.json({ success: true, doc });
  } catch (error: any) {
    console.error("Secure Log [GET /api/docs/:page]: Failed to load doc:", error);
    return NextResponse.json(
      { success: false, error: "An unexpected error occurred." },
      { status: 500 }
    );
  }
}
