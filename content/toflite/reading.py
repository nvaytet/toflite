# SPDX-License-Identifier: BSD-3-Clause

from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np

from .utils import Plot, NeutronData


@dataclass(frozen=True)
class ReadingField:
    name: str
    unit: str
    values: np.ndarray
    blocked_by_me: np.ndarray
    blocked_by_others: np.ndarray

    def plot(self, bins: int = 300, ax=None, **kwargs):
        if ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.get_figure()

        for i in range(len(self.values)):
            sel = ~self.blocked_by_others[i]
            x = self.values[i][sel]
            edges = np.linspace(x.min(), x.max(), bins + 1)
            mask = self.blocked_by_me[i][sel]
            if self.blocked_by_me[i].sum() > 0:
                ax.hist(
                    x[mask], bins=edges, histtype="step", lw=1.5, color="gray", **kwargs
                )
            ax.hist(
                x[~mask],
                bins=edges,
                histtype="step",
                lw=1.5,
                label=f"Pulse {i}",
                color=f"C{i}",
                **kwargs,
            )
        ax.legend()
        ax.set(xlabel=f"{self.name} [{self.unit}]", ylabel="Counts")
        return Plot(fig=fig, ax=ax)

    def min(self):
        mask = self.blocked_by_me | self.blocked_by_others
        return self.values[~mask].min()

    def max(self):
        mask = self.blocked_by_me | self.blocked_by_others
        return self.values[~mask].max()

    def __repr__(self) -> str:
        mask = self.blocked_by_me | self.blocked_by_others
        coord = self.values[~mask]
        return (
            f"{self.name} [{self.unit}]: min={coord.min()}, max={coord.max()}, "
            f"events={coord.size}"
        )

    def __str__(self) -> str:
        return self.__repr__()

    def __getitem__(self, val):
        return self.__class__(
            name=self.name,
            unit=self.unit,
            values=self.values[val],
            blocked_by_me=self.blocked_by_me[val],
            blocked_by_others=self.blocked_by_others[val],
        )


def _make_reading_field(data: NeutronData, field: str, unit: str) -> ReadingField:
    return ReadingField(
        name=field,
        unit=unit,
        values=getattr(data, field),
        blocked_by_me=data.blocked_by_me,
        blocked_by_others=data.blocked_by_others,
    )


class ComponentReading:
    """
    Data reading for a component placed in the beam path. The reading will have a
    record of the arrival times and wavelengths of the neutrons that passed through it.
    """

    @property
    def toa(self) -> ReadingField:
        return _make_reading_field(self.data, field="toa", unit="μs")

    @property
    def wavelength(self) -> ReadingField:
        return _make_reading_field(self.data, field="wavelength", unit="Å")

    @property
    def birth_time(self) -> ReadingField:
        return _make_reading_field(self.data, field="birth_time", unit="μs")

    @property
    def speed(self) -> ReadingField:
        return _make_reading_field(self.data, field="speed", unit="m/s")

    def plot(self, bins: int = 300) -> Plot:
        """
        Plot both the toa and wavelength data side by side.

        Parameters
        ----------
        bins:
            Number of bins to use for histogramming the neutrons.
        """
        fig, ax = plt.subplots(1, 2)
        self.toa.plot(bins=bins, ax=ax[0])
        self.wavelength.plot(bins=bins, ax=ax[1])
        fig.set_size_inches(10, 4)
        fig.tight_layout()
        return Plot(fig=fig, ax=ax)
