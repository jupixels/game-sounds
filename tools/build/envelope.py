"""Print an RMS envelope (dBFS) and onset list for an audio file, so cut points can be chosen without listening.
usage: python3 env.py FILE [hop_seconds] [start] [end]"""
import subprocess, sys
import numpy as np

def load(path, sr=22050):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32), sr

def main():
    path = sys.argv[1]
    hop = float(sys.argv[2]) if len(sys.argv) > 2 else 0.25
    x, sr = load(path)
    s = float(sys.argv[3]) if len(sys.argv) > 3 else 0
    e = float(sys.argv[4]) if len(sys.argv) > 4 else len(x) / sr
    x = x[int(s * sr):int(e * sr)]
    peak = np.max(np.abs(x)) + 1e-9
    print(f'{path}: {len(x)/sr:.2f}s peak {20*np.log10(peak):.1f} dBFS rms {20*np.log10(np.sqrt(np.mean(x**2))+1e-9):.1f}')
    n = int(hop * sr)
    rows = []
    for i in range(0, len(x) - n + 1, n):
        seg = x[i:i + n]
        rms = 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)
        pk = 20 * np.log10(np.max(np.abs(seg)) + 1e-9)
        rows.append((s + i / sr, rms, pk))
    for t, r, p in rows:
        bar = '#' * max(0, int((r + 60) / 1.5))
        print(f'{t:7.2f} rms{r:6.1f} pk{p:6.1f} {bar}')
    # onsets: 10ms frames whose energy jumps >12 dB above the previous 100 ms
    f = int(0.01 * sr)
    en = np.array([np.sqrt(np.mean(x[i:i + f] ** 2)) + 1e-9 for i in range(0, len(x) - f, f)])
    db = 20 * np.log10(en)
    ons, last = [], -1
    for i in range(10, len(db)):
        if db[i] - np.median(db[i - 10:i]) > 12 and db[i] > -40 and i - last > 15:
            ons.append((s + i * 0.01, db[i])); last = i
    print('onsets:', ' '.join(f'{t:.2f}({d:.0f})' for t, d in ons))

if __name__ == '__main__':
    main()
