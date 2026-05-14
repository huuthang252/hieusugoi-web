import OpenAI from "openai";
import { NextResponse } from "next/server";

const client = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(req: Request) {
  try {
    const body = await req.json();

    const text = body.text;

    if (!text) {
      return NextResponse.json(
        { error: "No text provided" },
        { status: 400 }
      );
    }
    const response = await client.chat.completions.create({
  model: "gpt-4.1-mini",
  messages: [
    {
      role: "system",
      content: `
Bạn là engine dịch thuật.

QUY TẮC:
- Chỉ trả về bản dịch tiếng Việt.
- Không giải thích.
- Không trò chuyện.
- Không hỏi lại.
- Không thêm ghi chú.
`
    },
    {
      role: "user",
      content: text
    }
  ]
});

return NextResponse.json({
  result: response.choices[0].message.content,
});
    

    return NextResponse.json({
      result: response.choices[0].message.content,
    });

  } catch (error) {
    console.error(error);

    return NextResponse.json(
      { error: "Server error" },
      { status: 500 }
    );
  }
}