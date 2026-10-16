# Storytelling Reel Editor: a Claude skill by Mino Lee (@minolee.mp4)

Send Claude a talking-to-camera clip and get back a finished, ready-to-post vertical reel:

- **Auto-captions** in TikTok Sans: 2-3 words at a time, clean white, no effects. Weight 600, tight spacing.
- **Simple animated UI above your head**, timed to your words: iOS notifications, app cards, a grid of your videos,
  an AI or app "talking back" in a chat bubble, and an Instagram comment box for your "Comment X" call to action.
- **Nothing under the TikTok/Reels buttons.** Every frame is checked so no text or graphic sits in the top 10%, the
  bottom 20%, or behind the like/comment/share column.
- **Audio done right:** your voice turned up to 200%. Background music sits at 25% during the song's quiet intro and
  drops to 10% the moment the drums kick in. A sound effect (like a vine boom) lands exactly on your word, and the
  music cuts on it.
- **It learns your taste.** Say "make that the default" and Claude saves it for every future edit.

This is the exact system I use for my own reels. Clip in, reel out, usually a few minutes per edit.

## What you need

- **Claude Code**: the "Code" tab in the Claude desktop app (or the `claude` terminal app). Needs a paid Claude plan.
- **A Mac** (Apple Silicon is fastest). Linux works too. On Windows, use WSL (not tested).
- **Google Chrome**, plus **ffmpeg**, **Node.js** and **Python 3** (Claude tells you exactly what's missing and the
  one-line command to install it).
- About 3 GB of free space (the speech-to-text model downloads once).

## Install (one prompt)

1. Download the skill. Leave it in your Downloads folder (zipped or unzipped, either is fine).
2. Open the Claude desktop app, click the **Code** tab, paste this, then drag your video in right after it and press
   Enter:

   > Install the storytelling-reel-editor skill from my Downloads folder into ~/.claude/skills, read its SKILL.md, run
   > its setup, and use it to edit this video:

Click **Allow** when Claude asks to run something. If it says Homebrew is missing, install it from https://brew.sh and
paste the prompt again. The first run also downloads the speech-to-text model (about 1.5 GB) once.

## Use it

After the first time, just ask. Some examples:

> Edit ~/Downloads/my-clip.mov with the storytelling reel editor.

> Caption ~/Downloads/clip.mov. When I say "getting views", pop up a TikTok notification that says "Your video is in
> 300 view jail...". Add a comment box for my CTA "Comment GUIDE", my handle is @yourhandle.

> Add ~/Music/song.m4a faintly in the background and a vine boom (~/Downloads/vine-boom.mp3) when I say "edited by
> Claude". Cut the song after the boom.

> Suggest 3 moments where a simple UI animation would help, show me the plan first.

Then give feedback like you would to an editor: "make the captions slightly bolder", "move that card lower",
"the music is too loud after the drums", "make that the default". Every version is kept (`-v1`, `-v2`...).

## Tips for the best result

- Film vertical (9:16), one continuous take. This skill doesn't cut your video: it captions and decorates it.
- iPhone HDR footage: export as SDR first (CapCut: turn HDR off; Photos: Share → Options → Most Compatible).
- Write joke text exactly how you want it shown, spelling included. Claude uses it word for word.
- Bring your own music and sound effects that you have the right to use. Major-label songs baked into a video can
  get muted, so for those, add the song inside the TikTok/Instagram app instead.

## What's inside

- `SKILL.md`: the instructions Claude follows.
- `reference/`: the style guide and the why behind every rule, the UI components, audio rules.
- `style.json`: every number (font, sizes, safe area, audio levels). Your saved preferences go here.
- `MY_STYLE.md`: a log of your style changes.
- `scripts/`: setup, transcription, captions, rendering, safe-area audit, audio mix, encode, QA.
- `template/`: the animation page Claude builds your graphics in.
- `fonts/`: TikTok Sans (free, open licence).

Made by Mino Lee · Instagram & TikTok: @minolee.mp4
