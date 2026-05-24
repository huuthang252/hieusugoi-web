import OpenAI from "openai";
import { NextResponse } from "next/server";

const ALLOWED_VOICES = ["nova", "onyx", "alloy", "echo", "fable", "shimmer"] as const;
type AllowedVoice = (typeof ALLOWED_VOICES)[number];

const client = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(req: Request) {
  let text: string;
  let voice: AllowedVoice = "nova";

  try {
    const body = (await req.json()) as {
      text?: unknown;
      voice?: unknown;
      format?: unknown;
    };

    if (!body.text || typeof body.text !== "string" || body.text.trim().length === 0) {
      return NextResponse.json({ error: "text is required" }, { status: 400 });
    }

    if (body.text.length > 500) {
      return NextResponse.json(
        { error: "text too long (max 500 characters)" },
        { status: 400 }
      );
    }

    text = body.text;

    if (body.voice !== undefined) {
      if (
        typeof body.voice !== "string" ||
        !ALLOWED_VOICES.includes(body.voice as AllowedVoice)
      ) {
        return NextResponse.json({ error: "invalid voice" }, { status: 400 });
      }
      voice = body.voice as AllowedVoice;
    }
  } catch {
    return NextResponse.json({ error: "invalid request body" }, { status: 400 });
  }

  console.log(`[TTS] request | text_len=${text.length} | voice=${voice}`);

  try {
    const response = await client.audio.speech.create({
      model: "gpt-4o-mini-tts",
      voice,
      input: text,
      response_format: "mp3",
    });

    const audioBuffer = Buffer.from(await response.arrayBuffer());

    console.log(`[TTS] success | bytes=${audioBuffer.length}`);

    return new Response(audioBuffer, {
      status: 200,
      headers: {
        "Content-Type": "audio/mpeg",
        "Content-Length": String(audioBuffer.length),
      },
    });
  } catch (error) {
    const errorType =
      error instanceof Error ? error.constructor.name : "UnknownError";
    console.error(`[TTS] error | type=${errorType}`);
    return NextResponse.json({ error: "TTS generation failed" }, { status: 500 });
  }
}
