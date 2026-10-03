"""
LectureFlow CLI — Universal AI Lecture Video Editing Pipeline
"""
import argparse
import sys
import os
import yaml
from pathlib import Path

from src.extractor import extract_slides_powerpoint
from src.transcriber import transcribe_audio
from src.cutter import detect_slide_cues, detect_retakes, build_right_to_left_cut_plan
from src.premiere_client import PremiereClient


def parse_args():
    parser = argparse.ArgumentParser(
        description="LectureFlow: Universal AI-Assisted Educational Video Editing Pipeline for Adobe Premiere Pro."
    )
    parser.add_argument("--video", "-v", required=True, help="Path to raw recorded footage (.mp4/.mov).")
    parser.add_argument("--ppt", "-p", required=True, help="Path to PowerPoint deck (.pptx).")
    parser.add_argument("--config", "-c", default="config.example.yaml", help="Path to configuration YAML.")
    parser.add_argument("--dry-run", action="store_true", help="Perform cue detection and cut planning without applying edits to Premiere.")
    return parser.parse_args()


def main():
    args = parse_args()
    print("=" * 70)
    print("  🎬 LectureFlow — Universal AI Lecture Video Editing Pipeline")
    print("=" * 70)

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"[-] Config file not found: {config_path}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 1. Slide Extraction
    print("\n[Step 1/5] Extracting slides from PowerPoint deck...")
    slide_dir = Path("extracted_slides")
    slide_dir.mkdir(parents=True, exist_ok=True)
    slides = extract_slides_powerpoint(
        ppt_path=args.ppt,
        output_dir=str(slide_dir),
        skip_first_n=config["slides"].get("skip_first_n", 2),
        skip_last_n=config["slides"].get("skip_last_n", 1),
    )
    print(f"[+] Successfully extracted and filtered {len(slides)} content slides.")

    # 2. Audio Transcription
    print("\n[Step 2/5] Transcribing audio with word-level timestamps...")
    audio_path = "temp_audio.wav"
    asr_engine = config["transcription"].get("engine", "faster-whisper")
    model_name = config["transcription"].get("model", "base.en")
    
    words = transcribe_audio(
        video_path=args.video,
        output_wav=audio_path,
        engine=asr_engine,
        model=model_name
    )
    print(f"[+] ASR complete: {len(words)} words transcribed with exact timestamps.")

    # 3. Cue & Retake Analysis
    print("\n[Step 3/5] Detecting slide transition cues & retakes...")
    cues = detect_slide_cues(words, total_slides=len(slides))
    retakes = detect_retakes(words, min_pause_seconds=config["editorial"].get("retake_pause_threshold_sec", 2.5))
    
    intro_offset = config["timing"].get("intro_offset_seconds", 12.72)
    cut_plan = build_right_to_left_cut_plan(cues, retakes, intro_offset_seconds=intro_offset)
    print(f"[+] Generated {len(cut_plan)} right-to-left cuts (zero timeline drift).")

    if args.dry_run:
        print("\n[Dry Run] Cut plan inspection:")
        for idx, cut in enumerate(cut_plan, start=1):
            print(f"  {idx}. Timeline {cut['timeline_cut_in']:.2f}s -> {cut['timeline_cut_out']:.2f}s | Reason: {cut['reason']}")
        print("\n[+] Dry run complete. Exiting without modifying Premiere Pro.")
        return

    # 4. Premiere Pro Execution
    print("\n[Step 4/5] Connecting to Adobe Premiere Pro Bridge...")
    pclient = PremiereClient()
    if not pclient.is_connected():
        print("[-] Could not connect to Premiere Pro bridge. Ensure Premiere Pro is open and MCP server is active.")
        sys.exit(1)

    print("[Step 5/5] Executing right-to-left ripple trimming and slide alignment...")
    pclient.execute_cut_plan(cut_plan)
    pclient.align_slides(slides, cues, intro_offset)
    pclient.apply_pip_layout(cues, config["pip"])
    
    print("\n" + "=" * 70)
    print("  ✅ LectureFlow Complete: Project is ready for final review and export!")
    print("=" * 70)


if __name__ == "__main__":
    main()
