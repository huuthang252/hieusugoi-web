export const JAPANESE_WORD_TRANSLATION_FORMAT = "japanese_word_translation";

type CompletionResponse = {
  choices?: Array<{
    finish_reason?: string | null;
    message?: {
      content?: string | null;
      refusal?: string | null;
    };
  }>;
};

type CompletionResult =
  | { ok: true; content: string | null }
  | { ok: false; status: 502; error: string };

const LEGACY_SYSTEM_INSTRUCTION = `
Bạn là engine dịch thuật.

QUY TẮC:
- Chỉ trả về bản dịch tiếng Việt.
- Không giải thích.
- Không trò chuyện.
- Không hỏi lại.
- Không thêm ghi chú.
`;

const JAPANESE_WORD_SYSTEM_INSTRUCTION =
  "You execute dictionary translation requests for Hieusugoi. Follow the user's " +
  "requested target language, output format, and field requirements exactly. " +
  "For a Japanese word response, the reading field must be non-empty and contain " +
  "the kana reading of the entire input. Return no commentary outside the JSON.";

const WORD_TRANSLATION_SCHEMA = {
  name: "japanese_word_translation",
  strict: true,
  schema: {
    type: "object",
    properties: {
      meaning: { type: "string" },
      reading: {
        type: "string",
        minLength: 1,
        description: "The non-empty kana reading of the entire Japanese input.",
      },
      example_source: { type: "string" },
      example_translation: { type: "string" },
    },
    required: [
      "meaning",
      "reading",
      "example_source",
      "example_translation",
    ],
    additionalProperties: false,
  },
} as const;

export const buildCompletionRequest = (
  text: string,
  outputFormat: unknown,
) => {
  const isJapaneseWord = outputFormat === JAPANESE_WORD_TRANSLATION_FORMAT;
  return {
    model: "gpt-4.1-mini",
    messages: [
      {
        role: "system" as const,
        content: isJapaneseWord
          ? JAPANESE_WORD_SYSTEM_INSTRUCTION
          : LEGACY_SYSTEM_INSTRUCTION,
      },
      { role: "user" as const, content: text },
    ],
    ...(isJapaneseWord
      ? {
          temperature: 0,
          response_format: {
            type: "json_schema" as const,
            json_schema: WORD_TRANSLATION_SCHEMA,
          },
        }
      : {}),
  };
};

export const extractCompletionResult = (
  response: CompletionResponse,
  outputFormat: unknown,
): CompletionResult => {
  const choice = response.choices?.[0];
  const message = choice?.message;
  if (outputFormat !== JAPANESE_WORD_TRANSLATION_FORMAT) {
    return { ok: true, content: message?.content ?? null };
  }

  if (message?.refusal) {
    return {
      ok: false,
      status: 502,
      error: "The translation model refused the structured request.",
    };
  }
  if (choice?.finish_reason !== "stop") {
    return {
      ok: false,
      status: 502,
      error: "The translation model returned an incomplete structured response.",
    };
  }
  if (typeof message?.content !== "string" || !message.content.trim()) {
    return {
      ok: false,
      status: 502,
      error: "The translation model returned no structured content.",
    };
  }
  return { ok: true, content: message.content };
};
