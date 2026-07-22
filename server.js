/**
 * Clip Studio — backend worker
 * ------------------------------------------------------------------
 * Two jobs:
 *   1) Cut a segment out of an uploaded source video and reformat it
 *      to vertical 1080x1920 (YouTube Shorts).
 *   2) Upload that clip to the connected YouTube channel via the Data API.
 *
 * Deploy this on a real server (Railway / Render / Fly). Do NOT run it on
 * Netlify/Vercel serverless functions — ffmpeg jobs exceed their timeouts.
 *
 * Token storage here is in-memory for simplicity. In production, persist the
 * OAuth refresh token per user (Supabase works well) so it survives restarts.
 */

import express from "express";
import cors from "cors";
import multer from "multer";
import { google } from "googleapis";
import ffmpegPath from "ffmpeg-static";
import ffmpeg from "fluent-ffmpeg";
import fs from "fs";
import os from "os";
import path from "path";
import crypto from "crypto";
import "dotenv/config";

ffmpeg.setFfmpegPath(ffmpegPath);

const app = express();
app.use(cors()); // lock this to your frontend origin in prod: cors({ origin: "https://yoursite" })
const upload = multer({ dest: os.tmpdir(), limits: { fileSize: 2 * 1024 * 1024 * 1024 } }); // 2GB

// --- OAuth client ---------------------------------------------------------
const oauth2 = new google.auth.OAuth2(
  process.env.GOOGLE_CLIENT_ID,
  process.env.GOOGLE_CLIENT_SECRET,
  process.env.REDIRECT_URI // e.g. https://your-worker.up.railway.app/oauth2callback
);

// Single-user token store. Swap for a per-user DB lookup in production.
let TOKENS = null;

// 1) Start the Google sign-in
app.get("/auth/youtube", (_req, res) => {
  const url = oauth2.generateAuthUrl({
    access_type: "offline",       // gets a refresh token
    prompt: "consent",
    scope: ["https://www.googleapis.com/auth/youtube.upload"],
  });
  res.redirect(url);
});

// 2) Google redirects back here with a code
app.get("/oauth2callback", async (req, res) => {
  try {
    const { tokens } = await oauth2.getToken(req.query.code);
    TOKENS = tokens; // persist this per-user in real life
    res.send("<h3>Connected. You can close this window.</h3>");
  } catch (e) {
    res.status(500).send("OAuth failed: " + e.message);
  }
});

// --- ffmpeg: cut + reformat to vertical -----------------------------------
function makeVerticalClip(srcPath, startSec, endSec) {
  return new Promise((resolve, reject) => {
    const out = path.join(os.tmpdir(), `clip_${crypto.randomUUID()}.mp4`);
    const dur = Math.max(0.5, endSec - startSec);
    ffmpeg(srcPath)
      .setStartTime(startSec)
      .duration(dur)
      // scale to fill 1080x1920 then center-crop (blurred-bar version is in the README)
      .videoFilters([
        "scale=1080:1920:force_original_aspect_ratio=increase",
        "crop=1080:1920",
      ])
      .outputOptions(["-c:v libx264", "-preset veryfast", "-crf 20", "-c:a aac", "-b:a 128k", "-movflags +faststart"])
      .on("end", () => resolve(out))
      .on("error", reject)
      .save(out);
  });
}

// --- YouTube upload -------------------------------------------------------
async function uploadToYouTube(filePath, meta) {
  if (!TOKENS) throw new Error("YouTube not connected");
  oauth2.setCredentials(TOKENS);
  const yt = google.youtube({ version: "v3", auth: oauth2 });

  const resp = await yt.videos.insert({
    part: ["snippet", "status"],
    requestBody: {
      snippet: {
        title: (meta.title || "Short").slice(0, 100),
        description: meta.description || "#Shorts",
        tags: meta.tags || ["shorts"],
        categoryId: "22",
      },
      status: {
        // Uploads from an UNVERIFIED app are force-locked to private by YouTube
        // regardless of what you set here. After your app passes Google's audit,
        // "public" (or "unlisted") will stick.
        privacyStatus: "public",
        selfDeclaredMadeForKids: false,
      },
    },
    media: { body: fs.createReadStream(filePath) },
  });
  return resp.data;
}

// --- Main endpoint the frontend calls -------------------------------------
app.post("/clip-and-upload", upload.single("source"), async (req, res) => {
  const cleanup = [];
  try {
    if (!req.file) throw new Error("No source video received");
    cleanup.push(req.file.path);
    const clip = JSON.parse(req.body.clip || "{}");
    const meta = JSON.parse(req.body.meta || "{}");

    const clipPath = await makeVerticalClip(req.file.path, Number(clip.in), Number(clip.out));
    cleanup.push(clipPath);

    const data = await uploadToYouTube(clipPath, meta);
    res.json({ videoId: data.id, privacyStatus: data.status?.privacyStatus, url: `https://youtube.com/shorts/${data.id}` });
  } catch (e) {
    res.status(500).send(e.message);
  } finally {
    for (const f of cleanup) fs.promises.unlink(f).catch(() => {});
  }
});

app.get("/", (_req, res) => res.send("Clip Studio worker is running."));

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => console.log(`Clip Studio worker on :${PORT}`));
