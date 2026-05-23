import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import path from "path";
import fs from "fs/promises";
import os from "os";

// Force Node.js runtime — required for fs, Buffer, and large multipart uploads
export const runtime = "nodejs";

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const file = formData.get("file") as File | null;

    if (!file) {
      return NextResponse.json({ error: "Missing file" }, { status: 400 });
    }

    // --- Robust metadata parsing ---
    // formData.get() can return a string OR a Blob depending on how the
    // multipart field was encoded by the client (requests library on Python
    // sends data fields as plain strings, but some HTTP clients wrap them as
    // Blobs). Handle both cases and always trim before JSON.parse.
    let metadata: Record<string, unknown> = {};
    const metadataRaw = formData.get("metadata");
    if (metadataRaw !== null) {
      try {
        const metadataStr =
          metadataRaw instanceof Blob
            ? (await metadataRaw.text()).trim()
            : String(metadataRaw).trim();
        if (metadataStr) {
          metadata = JSON.parse(metadataStr);
        }
      } catch (e) {
        console.warn(
          "[diagnostic] metadata parse failed:",
          e,
          "| raw type:",
          typeof metadataRaw,
          "| raw value (first 200):",
          String(metadataRaw).slice(0, 200)
        );
      }
    }

    // Generate a stable unique diagnostic ID
    const ts = new Date().toISOString().replace(/[:.]/g, "-");
    const rand = Math.random().toString(36).slice(2, 8);
    const diagnosticId = `diag_${ts}_${rand}`;

    // file_name = the original filename the client sent (e.g. diagnostic_20240523_143000.zip)
    // storage_path = unique path used inside the bucket (keyed by diagnosticId to avoid conflicts)
    const originalFileName = file.name || `${diagnosticId}.zip`;
    const storageName = `${diagnosticId}.zip`;
    const storageBucket = "diagnostic-logs";

    // Read file buffer ONCE — reused for both Supabase upload and temp fallback
    const fileBuffer = Buffer.from(await file.arrayBuffer());
    const fileSize = fileBuffer.byteLength;

    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

    let storagePath: string | null = null;

    if (supabaseUrl && serviceRoleKey) {
      try {
        const adminClient = createClient(supabaseUrl, serviceRoleKey, {
          auth: { persistSession: false },
        });

        // 1. Upload file to Supabase Storage
        const { error: storageError } = await adminClient.storage
          .from(storageBucket)
          .upload(storageName, fileBuffer, {
            contentType: "application/zip",
            upsert: false,
          });

        if (storageError) {
          console.error("[diagnostic] Storage upload failed:", storageError.message);
        } else {
          storagePath = storageName;
        }

        // 2. Insert row into diagnostic_logs
        //
        // Expected table schema (create once in Supabase SQL editor):
        //
        //   CREATE TABLE IF NOT EXISTS diagnostic_logs (
        //     id              TEXT PRIMARY KEY,
        //     storage_bucket  TEXT,
        //     storage_path    TEXT,
        //     file_name       TEXT,
        //     file_size       BIGINT,
        //     metadata        JSONB,
        //     username        TEXT,
        //     user_id         TEXT,
        //     app_version     TEXT,
        //     os_version      TEXT,
        //     issue_category  TEXT,
        //     created_at      TIMESTAMPTZ DEFAULT NOW()
        //   );
        const { error: dbError } = await adminClient
          .from("diagnostic_logs")
          .insert({
            id:             diagnosticId,
            storage_bucket: storageBucket,
            storage_path:   storagePath,
            file_name:      originalFileName,
            file_size:      fileSize,
            metadata:       metadata,
            username:       (metadata.username      as string) ?? null,
            user_id:        (metadata.user_id       as string) ?? null,
            app_version:    (metadata.app_version   as string) ?? null,
            os_version:     (metadata.os_version    as string) ?? null,
            issue_category: (metadata.issue_category as string) ?? "TTS",
          });

        if (dbError) {
          // Log clearly — table schema mismatch will show up here
          console.warn("[diagnostic] DB insert failed:", dbError.message);
        }
      } catch (err) {
        console.error("[diagnostic] Supabase operation failed:", err);
        // Fall through — still return diagnosticId so the client shows success
      }
    } else {
      // Fallback when Supabase env vars are not configured: save to temp dir
      console.warn("[diagnostic] Supabase env vars not set — falling back to temp dir");
      try {
        const tmpDir = path.join(os.tmpdir(), "hieusugoi-diagnostic");
        await fs.mkdir(tmpDir, { recursive: true });
        const savePath = path.join(tmpDir, storageName);
        await fs.writeFile(savePath, fileBuffer);
        storagePath = savePath;
        console.log("[diagnostic] Saved to temp path:", savePath);
      } catch (saveErr) {
        console.error("[diagnostic] Fallback save failed:", saveErr);
      }
    }

    return NextResponse.json({ diagnostic_id: diagnosticId });
  } catch (err) {
    console.error("[diagnostic] Unexpected error:", err);
    return NextResponse.json(
      { error: "Diagnostic upload failed", detail: String(err) },
      { status: 500 }
    );
  }
}
