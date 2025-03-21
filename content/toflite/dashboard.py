# SPDX-License-Identifier: BSD-3-Clause

import uuid
import matplotlib.pyplot as plt
import ipywidgets as ipw

from functools import partial
from itertools import chain
from mpl_toolkits.axes_grid1 import make_axes_locatable

from .source import Source
from .chopper import Chopper, Clockwise, AntiClockwise
from .detector import Detector
from .model import Model


class ChopperWidget(ipw.VBox):
    def __init__(self):
        self._uid = uuid.uuid4()
        self.frequency_widget = ipw.FloatText(
            description="Frequency", continuous_update=True
        )
        self.open_widget = ipw.Text(description="Open")
        self.close_widget = ipw.Text(description="Close")
        self.phase_widget = ipw.FloatText(description="Phase", continuous_update=True)
        self.distance_widget = ipw.FloatText(
            description="Distance", continuous_update=True
        )
        self.name_widget = ipw.Text(description="Name")
        self.direction_widget = ipw.Dropdown(
            options=["clockwise", "anti-clockwise"], description="Direction"
        )
        self.enabled_widget = ipw.Checkbox(
            value=True, indent=False, layout={"width": "100px"}
        )
        self.delete_widget = ipw.Button(
            icon="trash-alt", tooltip="Delete chopper", layout={"width": "40px"}
        )
        super().__init__(
            [
                self.name_widget,
                self.frequency_widget,
                self.open_widget,
                self.close_widget,
                self.phase_widget,
                self.distance_widget,
                self.direction_widget,
                ipw.HBox(
                    [
                        ipw.Label(value="Enabled"),
                        self.enabled_widget,
                        self.delete_widget,
                    ]
                ),
            ],
            layout={
                "border": "1px solid lightgray",
                "display": "flex",
                "flex_flow": "column",
                "align_items": "flex-end",
            },
        )

    def continuous_update(self, callback):
        self.frequency_widget.observe(callback, names="value")
        self.phase_widget.observe(callback, names="value")
        self.distance_widget.observe(callback, names="value")
        self.open_widget.observe(callback, names="value")
        self.close_widget.observe(callback, names="value")
        self.direction_widget.observe(callback, names="value")
        self.enabled_widget.observe(callback, names="value")


class DetectorWidget(ipw.VBox):
    def __init__(self):
        self._uid = uuid.uuid4()
        self.distance_widget = ipw.FloatText(
            description="Distance", continuous_update=True
        )
        self.name_widget = ipw.Text(description="Name")
        self.enabled_widget = ipw.Checkbox(
            value=True, indent=False, layout={"width": "100px"}
        )
        self.delete_widget = ipw.Button(
            icon="trash-alt", tooltip="Delete detector", layout={"width": "40px"}
        )
        super().__init__(
            [
                self.name_widget,
                self.distance_widget,
                ipw.HBox(
                    [
                        ipw.Label(value="Enabled"),
                        self.enabled_widget,
                        self.delete_widget,
                    ]
                ),
            ],
            layout={
                "border": "1px solid lightgray",
                "display": "flex",
                "flex_flow": "column",
                "align_items": "flex-end",
            },
        )

    def continuous_update(self, callback):
        self.distance_widget.observe(callback, names="value")
        self.enabled_widget.observe(callback, names="value")


class SourceWidget(ipw.VBox):
    def __init__(self):
        self.facility_widget = ipw.Dropdown(options=["ess"], description="Facility")
        self.neutrons_widget = ipw.IntText(value=100_000, description="Neutrons")
        self.pulses_widget = ipw.IntText(value=1, description="Pulses")
        super().__init__(
            [self.facility_widget, self.neutrons_widget, self.pulses_widget]
        )

    def continuous_update(self, callback):
        self.facility_widget.observe(callback, names="value")
        self.neutrons_widget.observe(callback, names="value")
        self.pulses_widget.observe(callback, names="value")


class TofWidget:
    def __init__(self):
        self.top_bar = ipw.HBox()

        self.run_button = ipw.Button(description="Run")
        self.continuous_update = ipw.Checkbox(
            description="Continuous update",
            value=False,
            indent=False,
            layout={"width": "180px"},
        )
        self.visible_rays = ipw.IntText(
            description="Visible rays",
            value=1000,
            continuous_update=True,
            layout={"width": "200px"},
        )
        self.blocked_rays = ipw.IntText(
            description="Blocked rays",
            value=0,
            continuous_update=True,
            layout={"width": "200px"},
        )
        with plt.ioff():
            self.time_distance_fig, self.time_distance_ax = plt.subplots(figsize=(8, 6))
            divider = make_axes_locatable(self.time_distance_ax)
            self.time_distance_cax = divider.append_axes("right", "4%", pad="5%")
            self.toa_wav_fig, self.toa_wav_ax = plt.subplots(1, 2, figsize=(11.5, 3.75))
            self.time_distance_fig.canvas.header_visible = False
            self.toa_wav_fig.canvas.header_visible = False
            self._legend_pick_connection = None

        self.source_widget = SourceWidget()
        self.source_widget.continuous_update(self.maybe_update)

        self.choppers_container = ipw.Accordion()
        self.add_chopper_button = ipw.Button(description="Add chopper")
        self.add_chopper_button.on_click(self.add_chopper)
        self.choppers_widget = ipw.VBox(
            [self.add_chopper_button, self.choppers_container]
        )

        self.detectors_container = ipw.Accordion()
        self.add_detector_button = ipw.Button(description="Add detector")
        self.add_detector_button.on_click(self.add_detector)
        self.detectors_widget = ipw.VBox(
            [self.add_detector_button, self.detectors_container]
        )

        tab_contents = ["Source", "Choppers", "Detectors"]
        children = [self.source_widget, self.choppers_widget, self.detectors_widget]
        self.tab = ipw.Tab(layout={"height": "650px", "width": "374px"})
        self.tab.children = children
        self.tab.titles = tab_contents
        self.top_bar.children = [
            ipw.VBox(
                [
                    ipw.HBox(
                        [
                            self.run_button,
                            self.continuous_update,
                            self.visible_rays,
                            self.blocked_rays,
                        ]
                    ),
                    self.time_distance_fig.canvas,
                ]
            ),
            self.tab,
        ]

        self.choppers_widget.children[0].on_click(self.add_chopper)
        self.detectors_widget.children[0].on_click(self.add_detector)
        self.run_button.on_click(self.run)
        self.visible_rays.observe(self.plot_time_distance, names="value")
        self.blocked_rays.observe(self.plot_time_distance, names="value")

        self.main_widget = ipw.VBox([self.top_bar, self.toa_wav_fig.canvas])

    def maybe_update(self, _):
        if self.continuous_update.value:
            self.run(None)
        else:
            self.run_button.style = {"button_color": "lightgreen"}

    def sync_chopper_titles(self, _):
        self.choppers_container.titles = tuple(
            f"{c.name_widget.value} ({int(c.frequency_widget.value)}Hz - "
            f"{c.distance_widget.value:.1f}m)"
            for c in self.choppers_container.children
        )

    def add_chopper(self, _):
        new_chopper = ChopperWidget()
        new_chopper.name_widget.observe(self.sync_chopper_titles)
        new_chopper.frequency_widget.observe(self.sync_chopper_titles, names="value")
        new_chopper.distance_widget.observe(self.sync_chopper_titles, names="value")
        new_chopper.delete_widget.on_click(
            partial(self.remove_chopper, uid=new_chopper._uid)
        )
        new_chopper.continuous_update(self.maybe_update)
        children = (*self.choppers_container.children, new_chopper)
        self.choppers_container.children = children
        self.choppers_container.selected_index = len(children) - 1

    def remove_chopper(self, _, uid):
        self.choppers_container.children = tuple(
            c for c in self.choppers_container.children if c._uid != uid
        )
        self.maybe_update(None)

    def sync_detector_titles(self, _):
        self.detectors_container.titles = tuple(
            f"{d.name_widget.value} ({d.distance_widget.value:.1f}m)"
            for d in self.detectors_container.children
        )

    def add_detector(self, _):
        new_detector = DetectorWidget()
        new_detector.name_widget.observe(self.sync_detector_titles, names="value")
        new_detector.distance_widget.observe(self.sync_detector_titles, names="value")
        new_detector.delete_widget.on_click(
            partial(self.remove_detector, uid=new_detector._uid)
        )
        new_detector.continuous_update(self.maybe_update)
        children = (*self.detectors_container.children, new_detector)
        self.detectors_container.children = children
        self.detectors_container.selected_index = len(children) - 1

    def remove_detector(self, _, uid):
        self.detectors_container.children = tuple(
            d for d in self.detectors_container.children if d._uid != uid
        )
        self.maybe_update(None)

    def plot_time_distance(self, _=None):
        self.time_distance_ax.clear()
        self.time_distance_cax.clear()
        self.results.plot(
            ax=self.time_distance_ax,
            cax=self.time_distance_cax,
            visible_rays=self.visible_rays.value,
            blocked_rays=self.blocked_rays.value,
        )
        self.time_distance_fig.tight_layout()

    def run(self, _):
        source = Source(
            facility=self.source_widget.facility_widget.value,
            neutrons=int(self.source_widget.neutrons_widget.value),
            pulses=int(self.source_widget.pulses_widget.value),
        )
        choppers = [
            Chopper(
                frequency=ch.frequency_widget.value,
                open=[float(v) for v in ch.open_widget.value.split(",")],
                close=[float(v) for v in ch.close_widget.value.split(",")],
                phase=ch.phase_widget.value,
                distance=ch.distance_widget.value,
                name=ch.name_widget.value,
                direction={"clockwise": Clockwise, "anti-clockwise": AntiClockwise}[
                    ch.direction_widget.value
                ],
            )
            for ch in self.choppers_container.children
            if ch.enabled_widget.value
        ]

        detectors = [
            Detector(distance=det.distance_widget.value, name=det.name_widget.value)
            for det in self.detectors_container.children
            if det.enabled_widget.value
        ]

        model = Model(source=source, choppers=choppers, detectors=detectors)
        self.results = model.run()
        self.plot_time_distance()

        components = sorted(
            chain(self.results.choppers.values(), self.results.detectors.values()),
            key=lambda c: c.distance,
        )

        self.toa_wav_ax[0].clear()
        self.toa_wav_ax[1].clear()
        if self._legend_pick_connection is not None:
            self.toa_wav_fig.canvas.mpl_disconnect(self._legend_pick_connection)
        for p in range(source.pulses):
            for i, c in enumerate(components):
                label = c.name if p == 0 else None
                toa = c.data.toa[p]
                wav = c.data.wavelength[p]
                sel = ~(c.data.blocked_by_me[p] | c.data.blocked_by_others[p])
                self.toa_wav_ax[0].hist(
                    toa[sel],
                    bins=300,
                    histtype="step",
                    lw=1.5,
                    color=f"C{i}",
                    label=label,
                )
                self.toa_wav_ax[1].hist(
                    wav[sel],
                    bins=300,
                    histtype="step",
                    lw=1.5,
                    color=f"C{i}",
                    label=label,
                )

        self.toa_wav_ax[0].set(xlabel="Time-of-arrival [μs]", ylabel="Counts")
        self.toa_wav_ax[1].set(xlabel="Wavelength [Å]", ylabel="Counts")
        self.toa_legend = self.toa_wav_ax[0].legend()
        self.wav_legend = self.toa_wav_ax[1].legend()
        self.toa_wav_fig.tight_layout()

        # Clickable legend
        self.map_legend_to_ax = {}
        for i, (toa_patch, wav_patch) in enumerate(
            zip(self.toa_legend.get_patches(), self.wav_legend.get_patches())
        ):
            toa_patch.set_picker(5)
            wav_patch.set_picker(5)
            self.map_legend_to_ax[toa_patch] = i
            self.map_legend_to_ax[wav_patch] = i
        self._legend_pick_connection = self.toa_wav_fig.canvas.mpl_connect(
            "pick_event", self.on_legend_pick
        )

        self.run_button.style = {"button_color": "#eeeeee"}

    def on_legend_pick(self, event):
        legend_patch = event.artist

        # Do nothing if the source of the event is not a legend line.
        if legend_patch not in self.map_legend_to_ax:
            return

        ind = self.map_legend_to_ax[legend_patch]
        for ax in self.toa_wav_ax:
            patch = ax.patches[ind]
            visible = not patch.get_visible()
            patch.set_visible(visible)
        alpha = 1.0 if visible else 0.2
        self.toa_legend.get_patches()[ind].set_alpha(alpha)
        self.wav_legend.get_patches()[ind].set_alpha(alpha)
        self.toa_wav_fig.canvas.draw_idle()


def app():
    return TofWidget().main_widget
