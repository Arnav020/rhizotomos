"""Pitch video: Kokoro TTS narration + animated slides + recorded live demo, assembled with ffmpeg.

Needs kokoro-onnx model files (kokoro-v1.0.int8.onnx, voices-v1.0.bin) in $KOKORO_DIR (default ../tts).
"""
import os
import subprocess
from pathlib import Path

import soundfile as sf
from kokoro_onnx import Kokoro
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
V = ROOT / "video"
B = V / "build"
B.mkdir(parents=True, exist_ok=True)
TTS = Path(os.environ.get("KOKORO_DIR", ROOT.parent / "tts"))
VOICE = os.environ.get("VOICE", "am_fenrir")

SCRIPT = [
    ("slide_01", "Around sixty A D, a Greek army physician named Dioscorides wrote De Materia Medica. For fifteen hundred years it was the pharmacology book of Europe, Byzantium and the Islamic world. Today we keep hearing that ancient remedies are being validated by science. This is Rhizotomos, named after the Greek root cutters Dioscorides learned from. It asks a sharper question. Which of these remedies has science actually tested, and which did it never test?"),
    ("slide_02", "Nobody can answer that today, for three reasons. First, names drift. The Greek thymon is not garden thyme, white hellebore is not a hellebore at all, and silphion is extinct. Second, popularity bias. Garlic appears in thousands of papers, so a naive search makes every claim about garlic look supported. Third, not all evidence is equal. A hundred test tube studies are not one clinical trial."),
    ("slide_03", "So we built an auditable pipeline on open data. We curated thirty four claims from De Materia Medica, each with its Greek name, a candidate modern species, and two explicit doubt flags. We resolved every species on the GBIF backbone taxonomy, ran more than two hundred PubMed queries, and held out European herbal monographs as an independent check. Every API response is cached, so anyone can rerun the analysis offline."),
    ("slide_04", "The method has four steps. Read the claim. Resolve the taxon. Weigh the evidence, dividing by each plant's total literature to cancel popularity. Then score the gap: a real preclinical signal, times the absence of trials, times our certainty in the identification. The key design choice is that every plant is compared with itself, paired with two unrelated uses as negative controls."),
    ("demo", "Here is the live atlas. Every point is one ancient claim. The orange points are translational gaps: plenty of laboratory work, and not a single human trial. Clicking a claim opens its full record: what Dioscorides wrote, the resolved species, the evidence tier, the lift over its own controls, the certainty, biodiversity records from GBIF, and a link to the exact PubMed query, so any judge can audit any number. The table can be searched and sorted by gap score."),
    ("slide_05", "The results. Only seventeen of thirty four claims ever reached a human clinical trial. Four are clear translational gaps, three were translated through an isolated compound, and two have no modern literature at all, including the lost silphion."),
    ("slide_06", "But is the signal real, or just famous plants? Twenty one of thirty three claims are more specific than their own negative controls, with a permutation p value of zero point zero one five. It survives removing uncertain identifications. And claims that match current European herbal monographs sit in higher evidence tiers, with an A U C of zero point eight two. Two thousand year old text and modern regulators agree more than chance would predict."),
    ("slide_07", "And here is a finding. Gentian root. Dioscorides wrote that it warms and is good for the stomach. In PubMed, that use is twelve times more specific than gentian's unrelated uses, with twenty papers, and zero clinical trials. Pomegranate against worms, black cumin for headache, and sage for wounds follow. These are hypotheses for prioritising trials, not medical claims."),
    ("slide_08", "Two insights we did not expect. GBIF matched every single name with ninety nine to one hundred percent confidence, even the disputed ones. Modern databases are confident. History is not. So we store that doubt as data. And the Papaver paradox: opium shows zero plant level trials for pain, although opioids are the most successful plant drugs ever. Evidence migrates into compounds, so we label those claims instead of calling them gaps."),
    ("slide_09", "We are explicit about limits. Co-occurrence measures research attention, not efficacy. Trial counts say nothing about results. The seed table needs verification against the critical edition. Several plants are highly toxic, and nothing here is medical advice. And because De Materia Medica is in the public domain, no living community's knowledge was taken."),
    ("slide_10", "Next, we will extract all eight hundred chapters with Greek language models, map names through Byzantine, Arabic and Latin translations, grade trial outcomes, and link species to compounds and conservation status. The method works for any historical pharmacopoeia. Rhizotomos turns two thousand years of recorded use into a ranked, auditable list of what science should test next."),
]


def tts():
    k = Kokoro(str(TTS / "kokoro-v1.0.int8.onnx"), str(TTS / "voices-v1.0.bin"))
    for name, text in SCRIPT:
        out = B / f"{name}.wav"
        if out.exists():
            continue
        samples, sr = k.create(text, voice=VOICE, speed=1.0, lang="en-us")
        sf.write(out, samples, sr)
        print("tts", name, round(len(samples) / sr, 1), "s")


def dur(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", str(path)]).decode().strip())


def record_demo(seconds):
    url = (ROOT / "docs" / "index.html").as_uri()
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1920, "height": 1080}, record_video_dir=str(B / "rec"),
                            record_video_size={"width": 1920, "height": 1080})
        pg = ctx.new_page()
        pg.goto(url); pg.wait_for_timeout(2500)
        pg.evaluate("document.getElementById('atlas').scrollIntoView({behavior:'smooth'})"); pg.wait_for_timeout(3500)
        for i in [1, 11, 24, 22]:  # opium, pomegranate, black cumin, gentian
            pg.evaluate(f"document.querySelector('.dot[data-i=\"{i}\"]').dispatchEvent(new MouseEvent('click',{{bubbles:true}}))")
            pg.wait_for_timeout(int(seconds * 1000 * 0.11))
        pg.mouse.wheel(0, 700); pg.wait_for_timeout(2000)
        pg.fill("#q", "wound"); pg.wait_for_timeout(2500); pg.fill("#q", ""); pg.wait_for_timeout(1000)
        pg.evaluate("document.getElementById('validation').scrollIntoView({behavior:'smooth'})")
        pg.wait_for_timeout(int(max(3000, seconds * 1000 * 0.25)))
        vid = pg.video.path(); ctx.close(); b.close()
    return Path(vid)


def main():
    tts()
    segs = []
    for name, _ in SCRIPT:
        wav = B / f"{name}.wav"
        d = dur(wav) + 1.0
        seg = B / f"seg_{name}.mp4"
        if name == "demo":
            raw = record_demo(d)
            vf = f"fps=30,scale=1920:1080,fade=t=in:st=0:d=0.4,fade=t=out:st={d-0.4:.2f}:d=0.4"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "1.5", "-i", str(raw), "-i", str(wav),
                            "-t", f"{d:.2f}", "-vf", vf, "-af", "adelay=300|300,apad",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-ar", "48000",
                            "-shortest", str(seg)], check=True)
        else:
            img = ROOT / "slides" / f"{name}.png"
            frames = int(d * 30)
            vf = (f"scale=3840:-1,zoompan=z='min(1+0.00025*on,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                  f":d={frames}:s=1920x1080:fps=30,fade=t=in:st=0:d=0.4,fade=t=out:st={d-0.4:.2f}:d=0.4")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(img), "-i", str(wav),
                            "-t", f"{d:.2f}", "-vf", vf, "-af", "adelay=300|300,apad",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-ar", "48000",
                            "-shortest", str(seg)], check=True)
        segs.append(seg)
        print("segment", name, round(d, 1), "s")
    lst = B / "list.txt"
    lst.write_text("".join(f"file '{s.as_posix()}'\n" for s in segs))
    out = V / "Rhizotomos_pitch.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(out)], check=True)
    print("video:", out, round(dur(out), 1), "s")


if __name__ == "__main__":
    main()
