"""
효과음 만들기 (표현 담당) - LMMS 로 만든 효과음 5종 x 2가지
  click : 버튼 누르기        (나무 '톡')
  card  : 카드 올려 놓기     (탁자에 종이 카드가 '착')
  hit   : 탄이 적에게 맞음   (둔탁한 타격)
  hurt  : 플레이어가 공격받음 (무거운 쿵 + 불협화음)
  clear : 스테이지 클리어    (하프/비브라폰 팡파레)
게임에서는 같은 효과음의 두 가지 중 하나를 무작위로 골라 틀어서 덜 반복적으로 들림.

하는 일: 짧은 LMMS 프로젝트(assets/sounds/lmms/*.mmp) 생성 → 렌더링 → 뒤쪽 무음 자르기·끝 페이드 → assets/sounds/*.wav
다시 만들기:  python assets/make_sfx.py   (LMMS 1.2 + numpy 필요, 게임 실행에는 필요 없음)
"""
import os
import subprocess

import numpy as np

import make_bgm as mb
from make_bgm import BEAT, key, preset, sampler, track

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "sounds")
PROJ_DIR = os.path.join(OUT_DIR, "lmms")
T = BEAT // 8             # 120 BPM 에서 6틱 ≈ 62ms (효과음 시간 단위)


def hit_(src, k=57, vol=100, pos=0, ln=24):
    """샘플 한 번 치기 → (트랙에 넣을 노트 목록)."""
    return [(pos, ln, k, vol)]


def notes(names, start=0, step=T, ln=T * 3, vol=90):
    """음 여러 개를 step 간격으로 차례로 (아르페지오)."""
    return [(start + i * step, ln, key(n), vol) for i, n in enumerate(names)]


# (이름, [(트랙 이름, 악기, 노트, 트랙 볼륨)], 리버브 양, 최종 크기)
SFX = [
    ("click_1", [("Rim", sampler("drums/rim01.ogg"), hit_(0, 62, 100), 90)], 0.08, 0.55),
    ("click_2", [("Clav", sampler("drums/clav01.ogg"), hit_(0, 60, 100), 90),
                 ("Tick", sampler("drums/hihat_closed05.ogg"), hit_(0, 64, 40), 50)], 0.08, 0.55),

    ("card_1", [("Paper", sampler("drums/hihat_closed02.ogg"), hit_(0, 48, 80), 80),
                ("Thump", sampler("drums/kick_soft01.ogg"), hit_(0, 62, 60), 55)], 0.05, 0.5),
    ("card_2", [("Snap", sampler("misc/snaph01.ogg"), hit_(0, 50, 85), 80),
                ("Brush", sampler("drums/hihat_closed05.ogg"), hit_(2, 43, 45), 45)], 0.05, 0.5),

    ("hit_1", [("Impact", sampler("misc/hit01.ogg"), hit_(0, 57, 100), 100),
               ("Body", sampler("drums/bassdrum_acoustic02.ogg"), hit_(0, 57, 80), 80)], 0.15, 0.8),
    ("hit_2", [("Impact", sampler("misc/hit02.ogg"), hit_(0, 55, 100), 100),
               ("Body", sampler("drums/kick_hard01.ogg"), hit_(0, 54, 70), 70)], 0.15, 0.8),

    ("hurt_1", [("Thud", sampler("drums/kick_distorted01.ogg"), hit_(0, 52, 90), 80),
                ("Brass", preset("OpulenZ/Brass.xpf"), [(2, T * 2, key("E3"), 90), (2, T * 2, key("F3"), 80),
                                                       (2 + T * 2, T * 4, key("D#3"), 90), (2 + T * 2, T * 4, key("E3"), 80)], 70)],
     0.2, 0.75),
    ("hurt_2", [("Thud", sampler("drums/bassdrum_acoustic01.ogg"), hit_(0, 50, 100), 100),
                ("Dong", sampler("misc/metalish_dong01.ogg"), hit_(0, 45, 70), 60)], 0.2, 0.75),

    ("clear_1", [("Harp", preset("OpulenZ/Harp.xpf"),
                  notes(["C5", "E5", "G5", "C6"]) + [(T * 4, T * 10, key(n), 85) for n in ("C5", "E5", "G5", "C6")], 85),
                 ("Bells", preset("OpulenZ/Bells.xpf"), [(T * 4, T * 8, key("C6"), 70), (T * 4, T * 8, key("G6"), 50)], 55)],
     0.35, 0.7),
    ("clear_2", [("Vibes", preset("OpulenZ/Vibraphone.xpf"),
                  notes(["D5", "F#5", "A5", "D6"], step=T, ln=T * 2) + [(T * 4, T * 10, key(n), 90) for n in ("D5", "F#5", "A5", "D6")], 90),
                 ("Brass", preset("OpulenZ/Brass.xpf"), [(T * 4, T * 8, key(n), 70) for n in ("D4", "A4", "D5")], 50)],
     0.35, 0.7),
]


# 효과음 종류별 최대 길이(초): 짧은 소리가 겹쳐서 지저분해지지 않게
MAX_LEN = {"click": 0.22, "card": 0.3, "hit": 0.55, "hurt": 0.8, "clear": 2.4}


def trim(data, rate, gain, max_len):
    """뒤쪽 무음 자르기 + 최대 길이 + 끝 페이드(길이의 1/4) + 크기 맞추기 (gain = 종류별 크기)."""
    level = np.abs(data).max(axis=1)
    loud = np.nonzero(level > np.abs(data).max() * 10 ** (-40 / 20))[0]
    end = min(len(data), (loud[-1] if len(loud) else 0) + int(0.02 * rate), int(max_len * rate))
    out = data[:end].copy()
    fade = min(len(out), max(int(0.02 * rate), len(out) // 4))
    out[len(out) - fade:] *= np.linspace(1, 0, fade)[:, None]
    # 크기: 평균 음량(RMS)을 맞춰서 두 가지 버전이 비슷하게 들리게, 단 최대치는 넘지 않게
    out *= gain * 32767 * 0.22 / max(1.0, np.sqrt((out ** 2).mean()))
    peak = np.abs(out).max()
    if peak > 32767 * 0.95:
        out *= 32767 * 0.95 / peak
    return out


def main():
    os.makedirs(PROJ_DIR, exist_ok=True)
    mb.TAIL_BARS = 1
    for name, parts, wet, gain in SFX:
        tracks = [track(t, inst, n, vol=v, length_bars=1) for t, inst, n, v in parts]
        mmp = os.path.join(PROJ_DIR, f"{name}.mmp")
        raw = os.path.join(PROJ_DIR, f"_{name}.wav")
        mb.project(120, 1, tracks, mmp, wet=wet, size=0.6)
        subprocess.run([mb.LMMS, "render", mmp, "-f", "wav", "-o", raw, "-s", "44100"], check=True, capture_output=True)
        rate, data = mb.read_wav(raw)
        os.remove(raw)
        out = trim(data, rate, gain, MAX_LEN[name.split("_")[0]])
        mb.write_wav(os.path.join(OUT_DIR, f"{name}.wav"), rate, out)
        print(f"저장: sounds/{name}.wav  ({len(out) / rate:.2f}초)")


if __name__ == "__main__":
    main()
