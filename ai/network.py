"""Neural network implementation."""

import math
import numpy as np
from config import N_IN, N_HID, N_OUT


class Network:
    def __init__(self, flat_weights: np.ndarray | None = None):
        if flat_weights is None:
            self.w1 = np.random.randn(N_IN, N_HID) * math.sqrt(2.0 / N_IN)
            self.b1 = np.zeros(N_HID)
            self.w2 = np.random.randn(N_HID, N_OUT) * math.sqrt(2.0 / N_HID)
            self.b2 = np.zeros(N_OUT)
        else:
            self.set_flat(flat_weights)

    def forward(self, x: np.ndarray) -> np.ndarray:
        hidden = np.tanh(x @ self.w1 + self.b1)
        return np.tanh(hidden @ self.w2 + self.b2)

    def get_flat(self) -> np.ndarray:
        return np.concatenate([self.w1.ravel(), self.b1.ravel(), self.w2.ravel(), self.b2.ravel()])

    def set_flat(self, flat: np.ndarray) -> None:
        i = 0
        n = N_IN * N_HID
        self.w1 = flat[i:i+n].reshape(N_IN, N_HID).copy()
        i += n
        n = N_HID
        self.b1 = flat[i:i+n].copy()
        i += n
        n = N_HID * N_OUT
        self.w2 = flat[i:i+n].reshape(N_HID, N_OUT).copy()
        i += n
        n = N_OUT
        self.b2 = flat[i:i+n].copy()
        i += n

    def clone(self) -> 'Network':
        return Network(self.get_flat())
