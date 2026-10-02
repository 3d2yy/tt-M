"""Generate a reproducible, known-pattern example without measurement data."""
import csv
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'test'))
from reference import correlate, DEFAULT_PATTERN, DEFAULT_WEIGHTS

rng = random.Random(42)
signal = [rng.randint(-3, 3) for _ in range(12)]
signal += [32 * sign + rng.randint(-3, 3) for sign in DEFAULT_PATTERN]
signal += [rng.randint(-3, 3) for _ in range(12)]
scores = correlate(signal, DEFAULT_WEIGHTS)
path = ROOT / 'build' / 'demo.csv'
path.parent.mkdir(exist_ok=True)
with path.open('w', newline='') as stream:
    writer = csv.writer(stream)
    writer.writerow(['sample_index', 'input_sample', 'correlation', 'hit'])
    for n, (sample, score) in enumerate(zip(signal, scores)):
        writer.writerow([n, sample, score, int(n >= 7 and score >= 160)])
hits = [(n, score) for n, score in enumerate(scores) if n >= 7 and score >= 160]
print('Patron insertado en muestras 12..19; indices desde cero.')
print(f'Detecciones (indice, puntuacion): {hits}')
print(f'Datos reproducibles: {path}')
