import OpenAI from "openai";
import { NextResponse } from "next/server";
import { createServerClient } from "@/lib/supabase-server";
import { isTranslateRequestAuthenticated } from "./auth";
import { buildCompletionRequest, extractCompletionResult } from "./completion";

const client = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

type TimingMarks = {
  received: number;
  authCompleted?: number;
  openAIStarted?: number;
  openAICompleted?: number;
  responsePrepared?: number;
  inputTokens?: number;
  outputTokens?: number;
};

const elapsed = (start: number, end: number | undefined): number =>
  Math.max(0, (end ?? performance.now()) - start);

const timingHeaders = (traceId: string, marks: TimingMarks): HeadersInit => {
  const responsePrepared = marks.responsePrepared ?? performance.now();
  const authCompleted = marks.authCompleted ?? marks.received;
  const openAIStarted = marks.openAIStarted ?? authCompleted;
  const openAICompleted = marks.openAICompleted ?? openAIStarted;
  const headers: Record<string, string> = {
    "Server-Timing": [
      `auth;dur=${elapsed(marks.received, authCompleted).toFixed(1)}`,
      `pre_openai;dur=${elapsed(authCompleted, openAIStarted).toFixed(1)}`,
      `openai;dur=${elapsed(openAIStarted, openAICompleted).toFixed(1)}`,
      `post_openai;dur=${elapsed(openAICompleted, responsePrepared).toFixed(1)}`,
      `backend_total;dur=${elapsed(marks.received, responsePrepared).toFixed(1)}`,
    ].join(", "),
    "X-Hieusugoi-Trace-Id": traceId,
  };
  if (marks.inputTokens !== undefined) {
    headers["X-Hieusugoi-Input-Tokens"] = String(marks.inputTokens);
  }
  if (marks.outputTokens !== undefined) {
    headers["X-Hieusugoi-Output-Tokens"] = String(marks.outputTokens);
  }
  return headers;
};

const timedJson = (
  body: unknown,
  init: { status?: number } | undefined,
  traceId: string,
  marks: TimingMarks,
) => {
  marks.responsePrepared = performance.now();
  const authCompleted = marks.authCompleted ?? marks.received;
  const openAIStarted = marks.openAIStarted ?? authCompleted;
  const openAICompleted = marks.openAICompleted ?? openAIStarted;
  console.info("translation_latency", {
    traceId,
    authMs: elapsed(marks.received, authCompleted),
    preOpenAIMs: elapsed(authCompleted, openAIStarted),
    openAIMs: elapsed(openAIStarted, openAICompleted),
    postOpenAIMs: elapsed(openAICompleted, marks.responsePrepared),
    backendTotalMs: elapsed(marks.received, marks.responsePrepared),
    inputTokens: marks.inputTokens,
    outputTokens: marks.outputTokens,
  });
  return NextResponse.json(body, {
    ...init,
    headers: timingHeaders(traceId, marks),
  });
};

export async function POST(req: Request) {
  const marks: TimingMarks = { received: performance.now() };
  const suppliedTraceId = req.headers.get("x-hieusugoi-trace-id") ?? "";
  const traceId = /^[a-f0-9]{32}$/i.test(suppliedTraceId)
    ? suppliedTraceId
    : crypto.randomUUID().replaceAll("-", "");
  const supabase = createServerClient();
  if (!(await isTranslateRequestAuthenticated(req, supabase))) {
    marks.authCompleted = performance.now();
    return timedJson({ error: "Unauthorized" }, { status: 401 }, traceId, marks);
  }
  marks.authCompleted = performance.now();

  try {
    const body = await req.json();

    const text = body.text;

    if (!text) {
      return timedJson(
        { error: "No text provided" },
        { status: 400 },
        traceId,
        marks,
      );
    }
    marks.openAIStarted = performance.now();
    const response = await client.chat.completions.create(
      buildCompletionRequest(text, body.output_format),
    );
    marks.openAICompleted = performance.now();
    marks.inputTokens = response.usage?.prompt_tokens;
    marks.outputTokens = response.usage?.completion_tokens;
    const completion = extractCompletionResult(response, body.output_format);
    if (!completion.ok) {
      return timedJson(
        { error: completion.error },
        { status: completion.status },
        traceId,
        marks,
      );
    }

    return timedJson(
      { result: completion.content },
      undefined,
      traceId,
      marks,
    );

  } catch (error) {
    console.error(error);

    return timedJson(
      { error: "Server error" },
      { status: 500 },
      traceId,
      marks,
    );
  }
}
