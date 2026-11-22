"""
배경음악 만들기 (표현 담당) - LMMS 로 만든 무한 반복 BGM 2곡
  title : 타이틀·설명·선택·결과 화면 (84 BPM, 4마디 ≈ 11.4초, D 단조, 하프 + 패드 + 클라리넷)
  game  : 플레이 화면 (140 BPM, 8마디 ≈ 13.7초, A 단조, 류트 + 베이스 + 백파이프 + 북)

하는 일
  1) 아래 악보 데이터로 LMMS 프로젝트(assets/music/*.mmp)를 만듦 → LMMS 에서 열어 고칠 수 있음
  2) LMMS 명령줄로 wav 렌더링 (반복 구간 뒤에 2마디 여유를 두고)
  3) 끝에서 넘친 잔향(여유 부분)을 앞부분에 겹쳐서, 끝 → 처음이 끊김 없이 이어지게 만듦
다시 만들기:  python assets/make_bgm.py   (LMMS 1.2 + numpy 필요, 게임 실행에는 필요 없음)
"""
import copy
import os
import subprocess
import wave
import xml.etree.ElementTree as ET

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "music")
LMMS = r"C:\Program Files\LMMS\lmms.exe"
PRESETS = r"C:\Program Files\LMMS\data\presets"
BAR = 192                 # LMMS 한 마디 = 192 틱 (4박, 한 박 = 48 틱)
BEAT = 48
TAIL_BARS = 2             # 잔향을 받기 위한 여유 마디
OUT_RATE = 22050          # 게임용 파일은 용량을 줄이려고 22kHz 로 저장

NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6,
        "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def key(name):
    """'A4' → LMMS 건반 번호 (C4 = 48, A4 = 57 = 440Hz)."""
    pitch, octave = name[:-1], int(name[-1])
    return 48 + NOTE[pitch] + (octave - 4) * 12


# ======================================================================
# 악기
# ======================================================================
def preset(path):
    """LMMS 프리셋(.xpf)의 instrumenttrack 요소."""
    root = ET.parse(os.path.join(PRESETS, path)).getroot()
    return copy.deepcopy(root.find("instrumenttracksettings/instrumenttrack"))


def sampler(src):
    """샘플 한 개를 그대로 내는 악기 (북 소리). basenote 57 에서 원래 높이."""
    it = ET.Element("instrumenttrack", pan="0", fxch="0", usemasterpitch="1", pitchrange="1",
                    pitch="0", basenote="57", vol="100")
    inst = ET.SubElement(it, "instrument", name="audiofileprocessor")
    ET.SubElement(inst, "audiofileprocessor", src=src, amp="100", reversed="0", looped="0",
                  sframe="0", lframe="0", eframe="1", stutter="0", interp="1")
    eld = ET.SubElement(it, "eldata", fres="0.5", ftype="0", fcut="14000", fwet="0")
    for tag in ("elvol", "elcut", "elres"):
        ET.SubElement(eld, tag, pdel="0", att="0", hold="0.5", dec="0.5", sustain="0.5", rel="0.1",
                      amt="0", x100="0", lamt="0", latt="0", lpdel="0", lshp="0", lspd="0.1",
                      lspd_numerator="4", lspd_denominator="4", lspd_syncmode="0", ctlenvamt="0", userwavefile="")
    ET.SubElement(it, "chordcreator", chord="0", chordrange="1", **{"chord-enabled": "0"})
    ET.SubElement(it, "arpeggiator", arp="0", arprange="1", arptime="100", arpgate="100", arpdir="0",
                  arpmode="0", **{"arp-enabled": "0"})
    ET.SubElement(it, "midiport", inputchannel="0", outputchannel="1", inputcontroller="0",
                  outputcontroller="0", fixedinputvelocity="-1", fixedoutputvelocity="-1",
                  fixedoutputnote="-1", outputprogram="1", basevelocity="63", readable="0", writable="0")
    return it


def track(name, instrument, notes, vol=100, pan=0, length_bars=4, release=None):
    """악기 트랙 하나 + 반복 구간 전체 길이의 패턴 하나."""
    t = ET.Element("track", muted="0", type="0", name=name, solo="0")
    instrument.set("vol", str(vol))
    instrument.set("pan", str(pan))
    if release is not None:                     # 음 끝 여운 (초)
        el = instrument.find("eldata/elvol")
        if el is not None:
            el.set("rel", str(release))
    fx = instrument.find("fxchain")
    if fx is not None:
        instrument.remove(fx)
    ET.SubElement(instrument, "fxchain", numofeffects="0", enabled="0")
    t.append(instrument)
    pat = ET.SubElement(t, "pattern", pos="0", len=str(length_bars * BAR), steps="16",
                        muted="0", type="1", name=name)
    for pos, length, k, v in notes:
        ET.SubElement(pat, "note", pos=str(int(pos)), len=str(int(length)), key=str(k), vol=str(v), pan="0")
    return t


def seq(items, start=0, vol=100):
    """[('E5', 박 길이), ...] → 노트 목록. 음 이름 대신 None 이면 쉼표."""
    out, pos = [], start
    for name, beats in items:
        if name:
            out.append((pos, beats * BEAT - 2, key(name), vol))
        pos += beats * BEAT
    return out


def project(bpm, bars, tracks, path, wet=0.35, size=0.86):
    """곡 프로젝트(.mmp) 저장. 마스터에 리버브, 반복 구간 표시, 끝에 잔향용 빈 마디."""
    root = ET.Element("lmms-project", version="1.0", creator="LMMS", creatorversion="1.2.2", type="song")
    ET.SubElement(root, "head", timesig_numerator="4", timesig_denominator="4", bpm=str(bpm),
                  mastervol="100", masterpitch="0")
    song = ET.SubElement(root, "song")
    tc = ET.SubElement(song, "trackcontainer", type="song", visible="1", x="5", y="5", width="600", height="300")
    for t in tracks:
        tc.append(t)
    # 잔향을 받을 빈 마디: 빈 트랙에 빈 패턴을 두어 곡 길이를 늘림
    empty = track("tail", sampler("drums/kick01.ogg"), [], vol=0, length_bars=TAIL_BARS)
    empty.find("pattern").set("pos", str(bars * BAR))
    tc.append(empty)
    mixer = ET.SubElement(song, "fxmixer", visible="0", x="0", y="0", width="500", height="300")
    master = ET.SubElement(mixer, "fxchannel", num="0", name="Master", volume="1", muted="0", soloed="0")
    chain = ET.SubElement(master, "fxchain", enabled="1", numofeffects="1")
    eff = ET.SubElement(chain, "effect", name="reverbsc", on="1", wet=str(wet), gate="0", autoquit="1",
                        autoquit_numerator="4", autoquit_denominator="4", syncmode="0")
    ET.SubElement(eff, "reverbsc", input_gain="0", size=str(size), color="9000", output_gain="0")
    ET.SubElement(eff, "key")
    ET.SubElement(song, "timeline", lp0pos="0", lp1pos=str(bars * BAR), lpstate="1")
    ET.SubElement(song, "controllers")
    tree = ET.ElementTree(root)
    ET.indent(tree)
    with open(path, "wb") as f:
        f.write(b'<?xml version="1.0"?>\n<!DOCTYPE lmms-project>\n')
        tree.write(f, encoding="utf-8")


# ======================================================================
# 곡 1: 타이틀 (D 단조, 84 BPM, 4마디) - 신비롭고 차분하게
# 코드 Dm - C - Bb - A  (마지막 A 가 다시 첫 Dm 으로 자연스럽게 돌아감)
# ======================================================================
def title_song():
    bars = 4
    chords = [["D3", "F3", "A3"], ["C3", "E3", "G3"], ["Bb2", "D3", "F3"], ["A2", "C#3", "E3"]]
    arps = [["D4", "A4", "D5", "F5", "A5", "F5", "D5", "A4"],
            ["C4", "G4", "C5", "E5", "G5", "E5", "C5", "G4"],
            ["Bb3", "F4", "Bb4", "D5", "F5", "D5", "Bb4", "F4"],
            ["A3", "E4", "A4", "C#5", "E5", "C#5", "A4", "E4"]]
    pad, harp, drum = [], [], []
    for b in range(bars):
        for n in chords[b]:
            pad.append((b * BAR, BAR - 4, key(n), 70))
        for i, n in enumerate(arps[b]):
            harp.append((b * BAR + i * 24, 40, key(n), 92 if i == 0 else 72))
        drum.append((b * BAR, 24, 57, 70))
        drum.append((b * BAR + 2.5 * BEAT, 24, 57, 40))
    melody = seq([("A5", 2), ("F5", 1), ("E5", 1),
                  ("E5", 1), ("G5", 1), ("E5", 2),
                  ("D5", 1), ("F5", 1), ("D5", 1), ("C5", 1),
                  ("C#5", 2), ("E5", 2)], vol=78)
    return 84, bars, [
        track("Pad", preset("OpulenZ/Pad.xpf"), pad, vol=45, length_bars=bars),
        track("Harp", preset("OpulenZ/Harp.xpf"), harp, vol=85, pan=-15, length_bars=bars),
        track("Clarinet", preset("OpulenZ/Clarinet.xpf"), melody, vol=55, pan=15, length_bars=bars, release=0.3),
        track("Drum", sampler("drums/bassdrum_acoustic01.ogg"), drum, vol=55, length_bars=bars),
    ]


# ======================================================================
# 곡 2: 게임 (A 단조, 140 BPM, 8마디) - 긴장감 있게 걷는 느낌
# 코드 Am - G - F - E 두 번 (E 가 다시 Am 으로 돌아감)
# ======================================================================
def game_song():
    bars = 8
    roots = ["A", "G", "F", "E"] * 2
    lute_pat = {"A": ["A3", "E4", "A4", "E4", "C5", "E4", "A4", "E4"],
                "G": ["G3", "D4", "G4", "D4", "B4", "D4", "G4", "D4"],
                "F": ["F3", "C4", "F4", "C4", "A4", "C4", "F4", "C4"],
                "E": ["E3", "B3", "E4", "B3", "G#4", "B3", "E4", "B3"]}
    lute, bass, dum, tek, hat = [], [], [], [], []
    for b, r in enumerate(roots):
        for i, n in enumerate(lute_pat[r]):
            lute.append((b * BAR + i * 24, 22, key(n), 88 if i % 2 == 0 else 66))
        low = key(r + "2")
        for pos, ln in ((0, 70), (72, 24), (96, 46), (144, 46)):       # 둥- 둥 둥 둥 (점음표 리듬)
            bass.append((b * BAR + pos, ln, low, 95))
        for pos in (0, 72, 96 + 48 * 1.5):                               # 북: 둥 (1박, 2박 반, 4박 반)
            dum.append((b * BAR + pos, 24, 57, 90))
        for pos in (48, 144):                                            # 탁: 2박, 4박
            tek.append((b * BAR + pos, 24, 57, 70))
        for i in range(8):                                               # 잔 방울 소리: 엇박
            if i % 2 == 1:
                hat.append((b * BAR + i * 24, 12, 57, 30))
    lead = seq([("E5", 1), ("A5", 1), ("G5", .5), ("F5", .5), ("E5", 1),
                ("D5", 1), ("G5", 1), ("F5", .5), ("E5", .5), ("D5", 1),
                ("C5", 1), ("F5", 1), ("E5", .5), ("D5", .5), ("C5", 1),
                ("B4", 1), ("E5", 1), ("G#5", 2),
                ("A5", 1.5), ("G5", .5), ("E5", 1), ("C5", 1),
                ("D5", 1.5), ("E5", .5), ("G5", 1), ("D5", 1),
                ("C5", 1), ("D5", .5), ("E5", .5), ("F5", 1), ("A5", 1),
                ("G#5", 1), ("B4", 1), ("E5", 2)], vol=80)
    return 140, bars, [
        track("Lute", preset("OpulenZ/Harp.xpf"), lute, vol=70, pan=-20, length_bars=bars),
        track("Bass", preset("BitInvader/subbass.xpf"), bass, vol=22, length_bars=bars),
        track("Bagpipe", preset("OpulenZ/Bagpipe.xpf"), lead, vol=95, pan=20, length_bars=bars, release=0.15),
        track("Dum", sampler("drums/bassdrum_acoustic01.ogg"), dum, vol=80, length_bars=bars),
        track("Tek", sampler("drums/rim01.ogg"), tek, vol=45, pan=10, length_bars=bars),
        track("Shaker", sampler("drums/hihat_closed03.ogg"), hat, vol=35, pan=-10, length_bars=bars),
    ]


# ======================================================================
# 렌더링 + 끊김 없는 반복 만들기
# ======================================================================
def read_wav(path):
    with wave.open(path) as w:
        rate, ch = w.getframerate(), w.getnchannels()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64)
    return rate, data.reshape(-1, ch)


def write_wav(path, rate, data):
    with wave.open(path, "wb") as w:
        w.setnchannels(data.shape[1])
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(np.clip(data, -32767, 32767).astype(np.int16).tobytes())


def make(name, song):
    bpm, bars, tracks = song
    mmp = os.path.join(OUT_DIR, f"{name}.mmp")
    raw = os.path.join(OUT_DIR, f"_{name}_raw.wav")
    project(bpm, bars, tracks, mmp)
    subprocess.run([LMMS, "render", mmp, "-f", "wav", "-o", raw, "-s", "44100", "-i", "sincmedium"],
                   check=True, capture_output=True)
    rate, data = read_wav(raw)
    os.remove(raw)
    loop = int(round(bars * 4 * 60 / bpm * rate))       # 반복 구간 길이 (샘플)
    body, tail = data[:loop].copy(), data[loop:]
    body[:len(tail)] += tail[:loop]                     # 끝에서 넘친 잔향을 처음에 겹침 → 이음매 없음
    body *= 0.89 * 32767 / max(1.0, np.abs(body).max())   # 소리 크기 맞추기 (-1dB)
    small = body[: len(body) // 2 * 2].reshape(-1, 2, body.shape[1]).mean(axis=1)   # 44.1k → 22.05k
    out = os.path.join(OUT_DIR, f"bgm_{name}.wav")
    write_wav(out, OUT_RATE, small)
    print(f"저장: {os.path.relpath(out, HERE)}  ({len(small) / OUT_RATE:.2f}초, {bpm}BPM {bars}마디)")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    make("title", title_song())
    make("game", game_song())


if __name__ == "__main__":
    main()
