# Gravity-as-Resonance — Proof of Concept
# VolkovLaw: F_res = K * sim(f1, f2) / r^2
# где sim — косинусная близость эмбеддингов "ядра" (core frequency)

from dataclasses import dataclass
import numpy as np

K = 1.0  # константа связи (подберём эмпирически)

def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a); nb = np.linalg.norm(b)
    if na == 0 or nb == 0: return 0.0
    return float(np.dot(a, b) / (na * nb))

@dataclass
class Particle:
    pos: np.ndarray          # (x, y, z)
    freq: np.ndarray         # вектор "ядра" (embedding / core frequency)
    mass_like: float = 1.0   # опционально: масштаб инерции (не «масса», а коэффициент отклика)

def resonance_force(p1: Particle, p2: Particle) -> np.ndarray:
    r_vec = p2.pos - p1.pos
    r = np.linalg.norm(r_vec)
    if r < 1e-9:  # защита
        return np.zeros(3)
    sim = cosine_sim(p1.freq, p2.freq)          # [-1..1]
    sim_pos = max(sim, 0.0)                      # отсекаем отталкивание (можно оставить, если нужно)
    mag = K * sim_pos / (r ** 2)                 # |F| ~ sim / r^2
    dir_vec = r_vec / r
    return mag * dir_vec

# ---------- Демонстрация ----------
if __name__ == "__main__":
    np.random.seed(42)

    # Три частицы с разными core-эмбеддингами
    p1 = Particle(pos=np.array([0.0, 0.0, 0.0]),
                  freq=np.array([0.9, 0.1, 0.0]))
    p2 = Particle(pos=np.array([1.0, 0.0, 0.0]),
                  freq=np.array([0.88, 0.12, 0.0]))
    p3 = Particle(pos=np.array([0.0, 1.0, 0.0]),
                  freq=np.array([-0.2, 0.98, 0.0]))

    # Силы p1 <- {p2, p3}
    F12 = resonance_force(p1, p2)
    F13 = resonance_force(p1, p3)
    F_total = F12 + F13

    print("cos(p1,p2) =", round(cosine_sim(p1.freq, p2.freq), 4))
    print("cos(p1,p3) =", round(cosine_sim(p1.freq, p3.freq), 4))
    print("F12:", F12)
    print("F13:", F13)
    print("F_total on p1:", F_total)

    # Мини-интегратор (Эйлер) — шаг 0.01, 100 шагов
    dt = 0.01
    v1 = np.zeros(3)
    for _ in range(100):
        F = resonance_force(p1, p2) + resonance_force(p1, p3)
        a = F / p1.mass_like
        v1 += a * dt
        p1.pos += v1 * dt
    print("p1.pos after 100 steps:", p1.pos)
