import assert from "node:assert/strict";
import test from "node:test";

import {
  buildCompletionRequest,
  extractCompletionResult,
  JAPANESE_WORD_TRANSLATION_FORMAT,
} from "../app/api/translate/completion.ts";


test("Japanese word requests require a complete structured reading response", () => {
  const request = buildCompletionRequest(
    "荷重計",
    JAPANESE_WORD_TRANSLATION_FORMAT,
  );

  assert.equal(request.temperature, 0);
  assert.match(request.messages[0].content, /reading field must be non-empty/);
  assert.equal(request.response_format.type, "json_schema");
  assert.equal(request.response_format.json_schema.strict, true);
  assert.equal(
    request.response_format.json_schema.schema.properties.reading.minLength,
    1,
  );
  assert.deepEqual(
    request.response_format.json_schema.schema.required,
    ["meaning", "reading", "example_source", "example_translation"],
  );
  assert.equal(
    request.response_format.json_schema.schema.additionalProperties,
    false,
  );
  assert.equal(request.messages[1].content, "荷重計");

  const invalidPayload = {
    meaning: "cân tải trọng",
    reading: "",
    example_source: "...",
    example_translation: "...",
  };
  const readingSchema =
    request.response_format.json_schema.schema.properties.reading;
  assert.equal(
    invalidPayload.reading.length >= readingSchema.minLength,
    false,
    "reading: '' violates the schema's minLength: 1 constraint",
  );
});


test("ordinary translations preserve the legacy free-text contract", () => {
  const request = buildCompletionRequest("Translate to English", undefined);

  assert.equal("response_format" in request, false);
  assert.equal("temperature" in request, false);
  assert.match(request.messages[0].content, /bản dịch tiếng Việt/);
});


test("completed Japanese structured content is returned as success", () => {
  const content =
    '{"meaning":"cân tải trọng","reading":"かじゅうけい",' +
    '"example_source":"...","example_translation":"..."}';
  const result = extractCompletionResult(
    {
      choices: [
        { finish_reason: "stop", message: { content, refusal: null } },
      ],
    },
    JAPANESE_WORD_TRANSLATION_FORMAT,
  );

  assert.deepEqual(result, { ok: true, content });
});


test("Japanese structured refusal is not returned as normal success", () => {
  const result = extractCompletionResult(
    {
      choices: [
        {
          finish_reason: "stop",
          message: { content: null, refusal: "synthetic refusal" },
        },
      ],
    },
    JAPANESE_WORD_TRANSLATION_FORMAT,
  );

  assert.equal(result.ok, false);
  assert.equal(result.status, 502);
  assert.match(result.error, /refused/);
});


test("incomplete Japanese structured completion is not normal success", () => {
  const result = extractCompletionResult(
    {
      choices: [
        { finish_reason: "length", message: { content: "{", refusal: null } },
      ],
    },
    JAPANESE_WORD_TRANSLATION_FORMAT,
  );

  assert.equal(result.ok, false);
  assert.equal(result.status, 502);
  assert.match(result.error, /incomplete/);
});


test("missing Japanese structured content is not normal success", () => {
  const result = extractCompletionResult(
    {
      choices: [
        { finish_reason: "stop", message: { content: null, refusal: null } },
      ],
    },
    JAPANESE_WORD_TRANSLATION_FORMAT,
  );

  assert.equal(result.ok, false);
  assert.equal(result.status, 502);
  assert.match(result.error, /no structured content/);
});


test("legacy completion extraction preserves pass-through behavior", () => {
  const result = extractCompletionResult(
    {
      choices: [
        { finish_reason: "length", message: { content: null, refusal: null } },
      ],
    },
    undefined,
  );

  assert.deepEqual(result, { ok: true, content: null });
});
