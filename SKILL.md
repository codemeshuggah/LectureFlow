---
name: LectureFlow
description: Universal, automated, and AI-assisted educational video editing pipeline for Adobe Premiere Pro. Automates slide extraction from PowerPoint, ASR word-level cue & retake detection, right-to-left ripple trimming, Ultra Key chroma keying, presenter Picture-in-Picture (PIP) layout, and seamless intro/outro integration.
---

# LectureFlow — Universal AI Lecture Video Editing Standard

**LectureFlow** is a modular, open-source automated video editing pipeline for educational course lectures, webinar recordings, and presentation videos inside **Adobe Premiere Pro** (interfacing via Model Context Protocol / Premiere Pro Bridge).

It transforms raw single-take green screen footage and presentation slide decks into broadcast-ready, tightly edited lecture videos in minutes.

---

## 🎯 What LectureFlow Automates

1. **Slide Deck Extraction & Direct-Filter Ingest**:
   - Extracts 1080p/4K PNG slides from `.pptx` presentations.
   - Filters out non-content cover slides and static "Thank You" slides during export.
   - Renames slides `Slide_01.png`, `Slide_02.png`, etc., ensuring 1:1 synchronization with spoken slide numbers.
   - Imports directly into a dedicated Premiere Pro project bin.

2. **Multi-Engine Speech-to-Text (ASR)**:
   - Extracts 16kHz mono audio via FFmpeg.
   - Transcribes speech with word-level timestamps using **Local Faster-Whisper** (offline, free, GPU-accelerated) or **ElevenLabs Scribe / OpenAI Whisper**.

3. **Verbal Cue & Retake Detection**:
   - Pinpoints spoken transition triggers (`"Slide one"`, `"Slide two"`, `"Next slide"`).
   - Detects verbal slips, retakes (`"Cut"`, `"Retake"`, stutter repetitions), and pauses exceeding natural cadence.
   - Computes natural in-cuts and out-cuts preserving organic room tone and speaker breathing (0.4s – 0.6s padding).

4. **Right-to-Left Ripple Trimming (Zero-Drift Guarantee)**:
   - Executes razor cuts and ripple deletes from **right to left** (chronologically latest cut to earliest).
   - Mathematically isolates downstream timeline shifts so upstream edit points remain permanently stationary.

5. **Chroma Keying & Presenter Picture-in-Picture (PIP)**:
   - Applies and auto-calibrates **Ultra Key** for clean green/blue screen background removal.
   - Formats the welcome greeting in full center (`100% Scale`).
   - Automatically transitions the presenter to a right- or left-aligned PIP (`66% Scale`) once the slide content begins.

6. **Track Architecture & Overlay Safety**:
   - Organizes assets across distinct video/audio layers.
   - Locks overlay tracks (e.g. Video 2) to protect lower thirds and graphical assets from accidental overwriting.
   - Keeps intro music beds permanently anchored at `00:00.00`.

---

## 🏗️ Timeline Track Architecture

```text
========================================================================================
[Video 5]  Transition Overlays & Mister Horse Adjustment Layers
[Video 4]  Graphic Callouts / Emphasized Keyframes
[Video 3]  Phase 1 Intro Cards (Logo Reveal, Instructor Card, Module Gap) + Keyed Presenter
[Video 2]  [LOCKED] Lower Thirds, Topic Banners & Subtitles
[Video 1]  Presenter Background Grid  |  Slide_01.png  |  Slide_02.png  |  OUTRO Video
========================================================================================
[Audio 1]  Raw Speaker Dialogue (synchronized 1:1 with Video 3 Presenter)
[Audio 2]  Intro Music Bed (permanently pinned at 00:00.00 – 00:14.24)
[Audio 3]  Transition Sound Effects (SFX / Whooshes)
========================================================================================
```

---

## 🚀 Execution Workflow

### Step 1: Pre-Edit Slide Ingest
- Export content slides from PowerPoint (`.pptx`) starting at Slide 3 up to $N-1$.
- Save as `Slide_01.png` to `Slide_{N}.png` in an asset directory.
- Import slides into Premiere Pro bin `SLIDES`.

### Step 2: Audio Extraction & Transcription
- Extract lightweight 16kHz mono audio from raw footage:
  ```bash
  ffmpeg -y -i "raw_footage.mp4" -vn -acodec pcm_s16le -ar 16000 -ac 1 "temp_audio.wav"
  ```
- Generate word-level timestamps using Whisper or ElevenLabs Scribe.

### Step 3: Verbal Cue & Retake Analysis
- Identify cue phrases:
  - Spoken slide numbers: `"Slide one"`, `"Slide two"`, etc.
  - Spoken edit signals: `"Cut"`, `"Take"`, `"Retake"`, long silences.
- Calculate exact cut intervals `[cut_in, cut_out]`.

### Step 4: Right-to-Left Trimming Execution
- Sort all cuts in descending chronological order:
  $$\text{Cut}_M, \text{Cut}_{M-1}, \ldots, \text{Cut}_1$$
- For each cut, execute `split_clip` or `ripple_delete` across targeted tracks (Video 3 & Audio 1).
- Because cuts proceed backwards, downstream timeline shifts never corrupt earlier cut timestamps.

### Step 5: PIP Motion Layout & Keying
- Split presenter clip at slide transition boundaries.
- Set Greeting clip:
  - Position: `(960, 540)` (1080p center)
  - Scale: `100.0%`
- Set Content Slide PIP clips:
  - Position: `(1520, 770)` (Right PIP) or configured layout
  - Scale: `66.0%`
- Apply `Ultra Key` effect to all keyed clips.

### Step 6: Slide Alignment & Outro Integration
- Place corresponding `Slide_XX.png` on Video 1 spanning the duration between consecutive slide cues.
- Trim raw footage tail at speaker wrap-up.
- Append Outro animation on Video 1 immediately following the last slide.
