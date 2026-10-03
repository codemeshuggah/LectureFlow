"""
LectureFlow Extractor
Extracts 16kHz mono audio from raw footage via FFmpeg,
and exports high-resolution content slides from PowerPoint (.pptx).
"""

import os
import sys
import subprocess
from typing import List

class MediaExtractor:
    @staticmethod
    def extract_audio(video_path: str, output_audio_path: str = "extracted_audio.mp3", sample_rate: int = 16000) -> str:
        """Extracts mono 16kHz audio from input video using FFmpeg."""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        print(f"[FFmpeg] Extracting audio from {os.path.basename(video_path)}...")
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vn",
            "-ac", "1",
            "-ar", str(sample_rate),
            output_audio_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg audio extraction failed:\n{res.stderr}")
        return output_audio_path

    @staticmethod
    def export_slides(
        pptx_path: str,
        output_dir: str,
        skip_cover_count: int = 2,
        skip_outro: bool = true,
        width: int = 1920,
        height: int = 1080
    ) -> List[str]:
        """
        Exports content slides from PowerPoint into output_dir as Slide_01.png, Slide_02.png, etc.
        Uses PowerShell COM on Windows for pixel-perfect vector font rasterization.
        """
        if not os.path.exists(pptx_path):
            raise FileNotFoundError(f"PowerPoint file not found: {pptx_path}")

        os.makedirs(output_dir, exist_ok=True)
        abs_pptx = os.path.abspath(pptx_path)
        abs_out = os.path.abspath(output_dir)

        if sys.platform == "win32":
            ps_script = f"""
            Add-Type -AssemblyName System.IO
            $pptApp = New-Object -ComObject PowerPoint.Application
            $pres = $pptApp.Presentations.Open('{abs_pptx}', [Microsoft.Office.Core.MsoTriState]::msoTrue, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
            $total = $pres.Slides.Count
            $endIdx = if ('{str(skip_outro).lower()}' -eq 'true') {{ $total - 1 }} else {{ $total }}
            $startIdx = {skip_cover_count + 1}
            $idx = 1
            for ($i = $startIdx; $i -le $endIdx; $i++) {{
                $slide = $pres.Slides.Item($i)
                $outName = Join-Path '{abs_out}' ("Slide_" + $idx.ToString("D2") + ".png")
                $slide.Export($outName, "PNG", {width}, {height})
                $idx++
            }}
            $pres.Close()
            $pptApp.Quit()
            [System.Runtime.Interopservices.Marshal]::ReleaseComObject($pptApp) | Out-Null
            """
            res = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
            if res.returncode != 0:
                raise RuntimeError(f"PowerPoint slide export failed: {res.stderr}")
        else:
            raise NotImplementedError("Direct PPTX rendering on non-Windows platforms requires LibreOffice or unoconv.")

        exported_files = sorted([
            os.path.join(output_dir, f)
            for f in os.listdir(output_dir)
            if f.startswith("Slide_") and f.endswith(".png")
        ])
        print(f"[Slides] Exported {len(exported_files)} content slides to {output_dir}")
        return exported_files
