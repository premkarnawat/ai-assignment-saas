#!/usr/bin/env python3
# handwriting-engine/test_render.py
"""
Quick test: renders a sample notebook page to output.png
Run from project root: python handwriting-engine/test_render.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from handwriting_renderer import HandwritingRenderer, RendererConfig

SAMPLE_TEXT = """CPU Scheduling

Introduction:
CPU Scheduling is the process by which the operating
system decides which process runs on the processor
at any given time.

Types of Scheduling Algorithms:
1. First Come First Serve (FCFS)
2. Shortest Job First (SJF)
3. Round Robin (RR)
4. Priority Scheduling

Round Robin:
Each process gets a fixed time slice called a quantum.
When the quantum expires, the process is placed at
the end of the ready queue.

Conclusion:
Efficient CPU scheduling is critical for maximising
processor utilisation and system throughput."""

if __name__ == "__main__":
    config = RendererConfig(
        font_name="Caveat",
        paper_type="notebook",
        base_font_size=26,
    )
    renderer = HandwritingRenderer(config)

    print("Rendering test page...")
    page = renderer.render_page(
        SAMPLE_TEXT,
        subject="Operating Systems",
        page_num=1,
    )

    output_path = "test_output.png"
    page.save(output_path, "PNG")
    print(f"✅ Saved to {output_path}")
    print(f"   Size: {page.size}")
