"""Classifier metrics for treating a harness module as a violation detector.

A module is, formally, a binary classifier over traces: *did the agent violate
the rule?* So we score it like one. The positive class is **violation** (the
module returns FAIL); the negative class is **compliant**.

    TP  violating trace, module said FAIL   (caught it)
    FP  compliant trace, module said FAIL   (false alarm)
    FN  violating trace, module stayed PASS  (missed it)
    TN  compliant trace, module stayed PASS  (correctly quiet)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Confusion:
    tp: int = 0
    fp: int = 0
    fn: int = 0
    tn: int = 0

    def add(self, *, truth_violating: bool, predicted_violating: bool) -> None:
        if truth_violating and predicted_violating:
            self.tp += 1
        elif not truth_violating and predicted_violating:
            self.fp += 1
        elif truth_violating and not predicted_violating:
            self.fn += 1
        else:
            self.tn += 1

    @property
    def n(self) -> int:
        return self.tp + self.fp + self.fn + self.tn

    @property
    def accuracy(self) -> float:
        return (self.tp + self.tn) / self.n if self.n else 0.0

    @property
    def precision(self) -> float:
        d = self.tp + self.fp
        return self.tp / d if d else 1.0

    @property
    def recall(self) -> float:
        d = self.tp + self.fn
        return self.tp / d if d else 1.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return (2 * p * r / (p + r)) if (p + r) else 0.0

    def merge(self, other: "Confusion") -> "Confusion":
        return Confusion(self.tp + other.tp, self.fp + other.fp,
                         self.fn + other.fn, self.tn + other.tn)

    def row(self) -> str:
        return (f"P={self.precision:.2f} R={self.recall:.2f} F1={self.f1:.2f} "
                f"acc={self.accuracy:.2f}  (TP{self.tp} FP{self.fp} FN{self.fn} TN{self.tn})")
