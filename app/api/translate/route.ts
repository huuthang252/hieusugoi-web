import OpenAI from "openai";
import { NextResponse } from "next/server";
import { createServerClient } from "@/lib/supabase-server";
import { isTranslateRequestAuthenticated } from "./auth";
import { buildCompletionRequest, extractCompletionResult } from "./completion";

const client = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(req: Request) {
  const supabase = createServerClient();
  if (!(await isTranslateRequestAuthenticated(req, supabase))) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const body = await req.json();

    const text = body.text;

    if (!text) {
      return NextResponse.json(
        { error: "No text provided" },
        { status: 400 }
      );
    }
    const response = await client.chat.completions.create(
      buildCompletionRequest(text, body.output_format),
    );
    const completion = extractCompletionResult(response, body.output_format);
    if (!completion.ok) {
      return NextResponse.json(
        { error: completion.error },
        { status: completion.status },
      );
    }

return NextResponse.json({
  result: completion.content,
});

  } catch (error) {
    console.error(error);

    return NextResponse.json(
      { error: "Server error" },
      { status: 500 }
    );
  }
}
