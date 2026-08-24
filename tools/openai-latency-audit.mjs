/* Direct OpenAI timing probe using the production request builder.
 * Prints only timing, token usage, and character counts—not prompts or outputs.
 */
import nextEnv from "@next/env";
import OpenAI from "openai";
import { performance } from "node:perf_hooks";

import {
  buildCompletionRequest,
  JAPANESE_WORD_TRANSLATION_FORMAT,
} from "../app/api/translate/completion.ts";


const { loadEnvConfig } = nextEnv;
loadEnvConfig(process.cwd());

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const cases = [
  "実施",
  "荷重計",
  "商事",
  "耐荷重",
  "取り込む",
  "彼は商事会社で働いています。",
];

const buildDesktopPrompt = (source, isWord) => {
  if (isWord) {
    return (
      "You are a concise dictionary translator.\n" +
      "Translate the word or short phrase below into Vietnamese.\n" +
      "Return only one valid JSON object with exactly these string fields:\n" +
      '{"meaning":"...","reading":"...","example_source":"...",' +
      '"example_translation":"..."}\n' +
      "Put the most natural concise meaning first. For Japanese, use a kana " +
      "reading; otherwise use an empty reading string when unnecessary. " +
      "Include one short natural source-language example and its Vietnamese " +
      "translation. Do not include additional fields or commentary.\n\n" +
      `Input:\n${source}`
    );
  }
  return (
    "You are a professional translator.\n" +
    "Translate the sentence or passage below naturally into Vietnamese.\n" +
    "Prioritize contextual correctness and natural phrasing. Return only the " +
    "translation, without commentary or labels.\n\n" +
    `Input:\n${source}`
  );
};

for (const [offset, source] of cases.entries()) {
  const isWord = offset < 5;
  const prompt = buildDesktopPrompt(source, isWord);
  const request = buildCompletionRequest(
    prompt,
    isWord ? JAPANESE_WORD_TRANSLATION_FORMAT : undefined,
  );
  const started = performance.now();
  try {
    const response = await client.chat.completions.create(request);
    const elapsedMs = performance.now() - started;
    const content = response.choices[0]?.message?.content ?? "";
    console.log(
      JSON.stringify({
        case: offset + 1,
        kind: isWord ? "word" : "sentence",
        model: response.model,
        elapsed_ms: Number(elapsedMs.toFixed(3)),
        input_tokens: response.usage?.prompt_tokens,
        output_tokens: response.usage?.completion_tokens,
        prompt_chars: prompt.length,
        output_chars: content.length,
      }),
    );
  } catch (error) {
    console.log(
      JSON.stringify({
        case: offset + 1,
        error_type: error?.constructor?.name ?? "Error",
        status: error?.status,
      }),
    );
  }
}
