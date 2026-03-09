from __future__ import annotations

import queue
import threading
import tkinter as tk
from datetime import datetime
from io import BytesIO
from tkinter import messagebox, ttk

import matplotlib.image as mpimg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from global_hazard_intel.domain.monitoring import MonitoringSnapshot
from global_hazard_intel.pipelines.orchestrator import HazardOrchestrator
from global_hazard_intel.reporting import ReportExporter

APP_TITLE = "GLOBAL HAZARD INTEL By Brian Gill"


class GlobalHazardIntelApp:
    def __init__(self) -> None:
        self.orchestrator = HazardOrchestrator()
        self.report_exporter = ReportExporter()
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry("1500x920")
        self.root.configure(bg="#08111d")

        self.query_mode_var = tk.StringVar(value="Continent")
        self.continent_var = tk.StringVar(value="Europe")
        self.query_var = tk.StringVar()
        self.latitude_var = tk.StringVar()
        self.longitude_var = tk.StringVar()
        self.interval_var = tk.StringVar(value="60")
        self.status_var = tk.StringVar(value="Ready")
        self.live_state_var = tk.StringVar(value="IDLE")
        self.region_var = tk.StringVar(value="No active region")
        self.last_update_var = tk.StringVar(value="Last update: --:--:--")
        self.hazard_count_var = tk.StringVar(value="0 hazards")
        self.priority_var = tk.StringVar(value="priority 0.00")

        self.snapshot_queue: queue.Queue[MonitoringSnapshot | Exception] = queue.Queue()
        self.monitoring_active = False
        self.fetch_in_progress = False
        self.current_snapshot: MonitoringSnapshot | None = None
        self.history: list[dict[str, float | str]] = []

        self._build_layout()
        self._refresh_input_state()
        self.root.after(1000, self._poll_queue)

    def _build_layout(self) -> None:
        shell = ttk.Frame(self.root, padding=14)
        shell.pack(fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#08111d")
        style.configure("TLabel", background="#08111d", foreground="#e7f0ff")
        style.configure("TLabelframe", background="#08111d", foreground="#7bd9ff")
        style.configure("TLabelframe.Label", background="#08111d", foreground="#7bd9ff")
        style.configure("TButton", padding=10, background="#123252", foreground="#f5fbff")
        style.map("TButton", background=[("active", "#1b4c7a")])
        style.configure("TCombobox", fieldbackground="#102238", background="#102238", foreground="#ffffff")
        style.configure("TEntry", fieldbackground="#102238", foreground="#ffffff")
        style.configure("Console.TLabelframe", background="#0b1727", foreground="#6fe7ff", borderwidth=1)
        style.configure("Console.TLabelframe.Label", background="#0b1727", foreground="#6fe7ff")
        style.configure("Console.TLabel", background="#0b1727", foreground="#dcecff")
        style.configure("Headline.TLabel", background="#08111d", foreground="#f4fbff", font=("Segoe UI Semibold", 18))
        style.configure("Subtle.TLabel", background="#08111d", foreground="#85a9cc", font=("Segoe UI", 9))
        style.configure("Metric.TLabel", background="#0b1727", foreground="#f4fbff", font=("Consolas", 16, "bold"))
        style.configure("MetricCaption.TLabel", background="#0b1727", foreground="#74dfff", font=("Segoe UI", 9))
        style.configure("Status.TLabel", background="#0b1727", foreground="#9af7c2", font=("Consolas", 11, "bold"))
        style.configure("TNotebook", background="#08111d", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(14, 8), background="#102238", foreground="#d8e6ff")
        style.map("TNotebook.Tab", background=[("selected", "#1a3350")], foreground=[("selected", "#7bd9ff")])

        header = ttk.Frame(shell)
        header.pack(fill="x", pady=(0, 10))

        title_block = ttk.Frame(header)
        title_block.pack(side="left", fill="x", expand=True)
        ttk.Label(title_block, text="GLOBAL HAZARD INTEL", style="Headline.TLabel").pack(anchor="w")
        ttk.Label(
            title_block,
            text="Advanced Environmental Hazard Analysis Console | Atmospheric, Health, and EO Operations",
            style="Subtle.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        metrics_bar = ttk.Frame(header)
        metrics_bar.pack(side="right")
        self._build_metric_card(metrics_bar, "STATE", self.live_state_var).pack(side="left", padx=(0, 8))
        self._build_metric_card(metrics_bar, "REGION", self.region_var, width=20).pack(side="left", padx=(0, 8))
        self._build_metric_card(metrics_bar, "HAZARDS", self.hazard_count_var, width=12).pack(side="left", padx=(0, 8))
        self._build_metric_card(metrics_bar, "PRIORITY", self.priority_var, width=14).pack(side="left", padx=(0, 8))
        self._build_metric_card(metrics_bar, "SYNC", self.last_update_var, width=18).pack(side="left")

        control = ttk.LabelFrame(shell, text="Mission Control", padding=12, style="Console.TLabelframe")
        control.pack(fill="x")

        ttk.Label(control, text="Query Type", style="Console.TLabel").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        mode_box = ttk.Combobox(
            control,
            textvariable=self.query_mode_var,
            values=["Continent", "Country", "City", "Address", "Coordinates"],
            state="readonly",
            width=18,
        )
        mode_box.grid(row=0, column=1, sticky="w", padx=6, pady=6)
        mode_box.bind("<<ComboboxSelected>>", lambda _: self._refresh_input_state())

        self.continent_box = ttk.Combobox(
            control,
            textvariable=self.continent_var,
            values=["Europe", "Asia", "North America", "South America", "Africa", "Australia"],
            state="readonly",
            width=24,
        )
        self.continent_box.grid(row=0, column=2, sticky="w", padx=6, pady=6)

        ttk.Label(control, text="Text Query", style="Console.TLabel").grid(row=0, column=3, sticky="w", padx=6, pady=6)
        self.query_entry = ttk.Entry(control, textvariable=self.query_var, width=36)
        self.query_entry.grid(row=0, column=4, sticky="we", padx=6, pady=6)

        ttk.Label(control, text="Latitude", style="Console.TLabel").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        self.latitude_entry = ttk.Entry(control, textvariable=self.latitude_var, width=18)
        self.latitude_entry.grid(row=1, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(control, text="Longitude", style="Console.TLabel").grid(row=1, column=2, sticky="w", padx=6, pady=6)
        self.longitude_entry = ttk.Entry(control, textvariable=self.longitude_var, width=18)
        self.longitude_entry.grid(row=1, column=3, sticky="w", padx=6, pady=6)

        ttk.Label(control, text="Refresh Seconds", style="Console.TLabel").grid(row=1, column=4, sticky="w", padx=6, pady=6)
        ttk.Entry(control, textvariable=self.interval_var, width=10).grid(row=1, column=5, sticky="w", padx=6, pady=6)

        ttk.Button(control, text="Start Live Detection", command=self.start_monitoring).grid(
            row=0, column=5, sticky="e", padx=6, pady=6
        )
        ttk.Button(control, text="Stop", command=self.stop_monitoring).grid(
            row=0, column=6, sticky="e", padx=6, pady=6
        )
        ttk.Button(control, text="Make Report", command=self.export_report).grid(
            row=1, column=6, sticky="e", padx=6, pady=6
        )

        ttk.Label(control, textvariable=self.status_var, style="Status.TLabel").grid(
            row=2, column=0, columnspan=7, sticky="w", padx=6, pady=(10, 0)
        )
        control.columnconfigure(4, weight=1)

        content = ttk.Panedwindow(shell, orient="horizontal")
        content.pack(fill="both", expand=True, pady=(12, 0))

        left = ttk.Frame(content)
        right = ttk.LabelFrame(content, text="Analysis Briefing", padding=12, style="Console.TLabelframe")
        content.add(left, weight=4)
        content.add(right, weight=2)

        self.figure = Figure(figsize=(12.5, 7.5), dpi=100, facecolor="#08111d")
        self.ax_hazards = self.figure.add_subplot(221)
        self.ax_trends = self.figure.add_subplot(222)
        self.ax_map = self.figure.add_subplot(223)
        self.ax_metrics = self.figure.add_subplot(224)
        self._style_axes()

        self.canvas = FigureCanvasTkAgg(self.figure, master=left)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        notebook = ttk.Notebook(right)
        notebook.pack(fill="both", expand=True)

        self.info_text = self._build_text_panel(notebook)
        self.weather_text = self._build_text_panel(notebook)
        self.health_text = self._build_text_panel(notebook)
        self.science_text = self._build_text_panel(notebook)
        self.forecast_text = self._build_text_panel(notebook)
        self.executive_text = self._build_text_panel(notebook)

        notebook.add(self.info_text, text="Overview")
        notebook.add(self.weather_text, text="Weather")
        notebook.add(self.health_text, text="Health")
        notebook.add(self.science_text, text="Scientific")
        notebook.add(self.forecast_text, text="Forecast")
        notebook.add(self.executive_text, text="Executive")

        self.root.bind("<Return>", lambda _: self.start_monitoring())
        self.root.bind("<Escape>", lambda _: self.stop_monitoring())

    def _build_metric_card(self, parent: ttk.Frame, title: str, variable: tk.StringVar, width: int = 14) -> ttk.Frame:
        frame = ttk.LabelFrame(parent, text=title, padding=8, style="Console.TLabelframe")
        ttk.Label(frame, textvariable=variable, style="Metric.TLabel", width=width).pack(anchor="w")
        return frame

    def _build_text_panel(self, parent: ttk.Notebook) -> tk.Text:
        return tk.Text(
            parent,
            width=48,
            height=30,
            bg="#0f1d31",
            fg="#e7f0ff",
            insertbackground="#e7f0ff",
            wrap="word",
            relief="flat",
        )

    def _style_axes(self) -> None:
        for axis in [self.ax_hazards, self.ax_trends, self.ax_map, self.ax_metrics]:
            axis.set_facecolor("#102238")
            axis.tick_params(colors="#d8e6ff")
            axis.title.set_color("#7bd9ff")
            for spine in axis.spines.values():
                spine.set_color("#33557f")

    def _refresh_input_state(self) -> None:
        mode = self.query_mode_var.get()
        if mode == "Continent":
            self.continent_box.configure(state="readonly")
            self.query_entry.configure(state="disabled")
            self.latitude_entry.configure(state="disabled")
            self.longitude_entry.configure(state="disabled")
        elif mode == "Coordinates":
            self.continent_box.configure(state="disabled")
            self.query_entry.configure(state="disabled")
            self.latitude_entry.configure(state="normal")
            self.longitude_entry.configure(state="normal")
        else:
            self.continent_box.configure(state="disabled")
            self.query_entry.configure(state="normal")
            self.latitude_entry.configure(state="disabled")
            self.longitude_entry.configure(state="disabled")

    def start_monitoring(self) -> None:
        try:
            interval = max(10, int(self.interval_var.get()))
        except ValueError:
            messagebox.showerror(APP_TITLE, "Refresh seconds must be a number.")
            return

        query, mode = self._resolve_query()
        if not query:
            messagebox.showerror(APP_TITLE, "Please provide a valid location query.")
            return

        self.monitoring_active = True
        self.live_state_var.set("LIVE")
        self.status_var.set(f"Starting live detection for {query}")
        self.region_var.set(query)
        if not self.fetch_in_progress:
            self._run_detection_thread(query, mode)
        self._schedule_next_poll(interval)

    def stop_monitoring(self) -> None:
        self.monitoring_active = False
        self.live_state_var.set("STOPPED")
        self.status_var.set("Monitoring stopped")

    def export_report(self) -> None:
        if self.current_snapshot is None:
            messagebox.showwarning(APP_TITLE, "Run a live detection first.")
            return

        report_dir = self.report_exporter.export(self.current_snapshot, self.figure)
        self.status_var.set(f"Report exported to {report_dir}")
        messagebox.showinfo(APP_TITLE, f"Report saved in:\n{report_dir}")

    def _schedule_next_poll(self, interval: int) -> None:
        if not self.monitoring_active:
            return
        self.root.after(interval * 1000, self._polling_tick)

    def _polling_tick(self) -> None:
        if not self.monitoring_active:
            return
        query, mode = self._resolve_query()
        if not self.fetch_in_progress:
            self._run_detection_thread(query, mode)
        try:
            interval = max(10, int(self.interval_var.get()))
        except ValueError:
            interval = 60
        self._schedule_next_poll(interval)

    def _run_detection_thread(self, query: str, mode: str) -> None:
        self.fetch_in_progress = True
        thread = threading.Thread(target=self._fetch_snapshot, args=(query, mode), daemon=True)
        thread.start()

    def _fetch_snapshot(self, query: str, mode: str) -> None:
        try:
            snapshot = self.orchestrator.run_snapshot(query, mode=mode)
            self.snapshot_queue.put(snapshot)
        except Exception as error:
            self.snapshot_queue.put(error)

    def _poll_queue(self) -> None:
        try:
            item = self.snapshot_queue.get_nowait()
        except queue.Empty:
            self.root.after(1000, self._poll_queue)
            return

        if isinstance(item, Exception):
            self.live_state_var.set("ERROR")
            self.status_var.set(f"Error: {item}")
            messagebox.showerror(APP_TITLE, str(item))
        else:
            self.current_snapshot = item
            self._append_history(item)
            self._update_dashboard(item)
            self.live_state_var.set("LIVE")
            self.region_var.set(item.location.display_name[:28])
            self.hazard_count_var.set(f"{len(item.hazards)} hazards")
            self.priority_var.set(f"{item.analytics.executive.enterprise_priority_score:.2f}")
            self.last_update_var.set(datetime.now().strftime("%H:%M:%S"))
            self.status_var.set(
                f"Live snapshot updated at {datetime.now().strftime('%H:%M:%S')} for {item.location.display_name}"
            )
        self.fetch_in_progress = False

        self.root.after(1000, self._poll_queue)

    def _append_history(self, snapshot: MonitoringSnapshot) -> None:
        top_severity = max((hazard.severity for hazard in snapshot.hazards), default=0.0)
        avg_confidence = (
            sum(hazard.confidence for hazard in snapshot.hazards) / len(snapshot.hazards)
            if snapshot.hazards
            else 0.0
        )
        self.history.append(
            {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "top_severity": top_severity,
                "avg_confidence": avg_confidence,
                "aqi": float(snapshot.air_quality.get("us_aqi") or 0.0),
            }
        )
        self.history = self.history[-20:]

    def _update_dashboard(self, snapshot: MonitoringSnapshot) -> None:
        self._draw_hazard_bars(snapshot)
        self._draw_trends()
        self._draw_map(snapshot)
        self._draw_metric_panel(snapshot)
        self._update_info_panel(snapshot)
        self.figure.tight_layout(pad=2.0)
        self.canvas.draw_idle()

    def _draw_hazard_bars(self, snapshot: MonitoringSnapshot) -> None:
        self.ax_hazards.clear()
        self.ax_hazards.set_facecolor("#102238")
        labels = [hazard.hazard_type.value.replace("_", "\n") for hazard in snapshot.hazards] or ["no\nhazard"]
        values = [hazard.severity for hazard in snapshot.hazards] or [0.0]
        colors = ["#ff6b57", "#ff9e44", "#f4d35e", "#5edfff"][: len(values)] or ["#5edfff"]
        self.ax_hazards.bar(labels, values, color=colors)
        self.ax_hazards.set_ylim(0, 1.0)
        self.ax_hazards.set_title("Hazard Severity Matrix")
        self.ax_hazards.set_ylabel("Severity")
        self.ax_hazards.grid(axis="y", color="#28425e", alpha=0.45, linestyle=":")

    def _draw_trends(self) -> None:
        self.ax_trends.clear()
        self.ax_trends.set_facecolor("#102238")
        if not self.history:
            self.ax_trends.set_title("Live Trend History")
            return
        times = [item["timestamp"] for item in self.history]
        severities = [float(item["top_severity"]) for item in self.history]
        aqi = [float(item["aqi"]) for item in self.history]
        self.ax_trends.plot(times, severities, color="#7bd9ff", marker="o", label="Top Severity")
        self.ax_trends.plot(times, [min(1.0, value / 300.0) for value in aqi], color="#ffb347", marker="o", label="US AQI / 300")
        self.ax_trends.set_ylim(0, 1.05)
        self.ax_trends.set_title("Temporal Detection Trend")
        self.ax_trends.tick_params(axis="x", rotation=35)
        self.ax_trends.legend(facecolor="#102238", edgecolor="#33557f", labelcolor="#e7f0ff")
        self.ax_trends.grid(color="#28425e", alpha=0.35, linestyle=":")

    def _draw_map(self, snapshot: MonitoringSnapshot) -> None:
        self.ax_map.clear()
        self.ax_map.set_facecolor("#102238")
        image = self._read_image(snapshot.satellite_image_bytes) if snapshot.satellite_image_bytes else None
        if image is not None:
            self.ax_map.imshow(image)
            self.ax_map.scatter(image.shape[1] / 2, image.shape[0] / 2, s=60, c="#ff5c5c", marker="x")
            self.ax_map.set_title("Satellite Reconnaissance View")
            self.ax_map.set_xticks([])
            self.ax_map.set_yticks([])
        else:
            self.ax_map.set_title("Geospatial Fallback View")
            self.ax_map.scatter(snapshot.location.longitude, snapshot.location.latitude, c="#ff5c5c", s=80)
            self.ax_map.set_xlim(snapshot.location.longitude - 5, snapshot.location.longitude + 5)
            self.ax_map.set_ylim(snapshot.location.latitude - 5, snapshot.location.latitude + 5)
            self.ax_map.set_xlabel("Longitude")
            self.ax_map.set_ylabel("Latitude")
        self.ax_map.text(
            0.02,
            0.04,
            snapshot.location.display_name[:52],
            transform=self.ax_map.transAxes,
            color="#f4fbff",
            fontsize=9,
            bbox={"facecolor": "#08111d", "edgecolor": "#33557f", "alpha": 0.75, "pad": 4},
        )

    def _draw_metric_panel(self, snapshot: MonitoringSnapshot) -> None:
        self.ax_metrics.clear()
        self.ax_metrics.set_facecolor("#102238")
        metrics = {
            "US AQI": min(1.0, float(snapshot.air_quality.get("us_aqi") or 0.0) / 300.0),
            "PM2.5": min(1.0, float(snapshot.air_quality.get("pm2_5") or 0.0) / 150.0),
            "Dust": min(1.0, float(snapshot.air_quality.get("dust") or 0.0) / 300.0),
            "Wind": min(1.0, float(snapshot.weather.get("wind_speed_10m") or 0.0) / 80.0),
            "SO2": min(1.0, float(snapshot.air_quality.get("sulphur_dioxide") or 0.0) / 350.0),
        }
        self.ax_metrics.barh(list(metrics.keys()), list(metrics.values()), color="#5edfff")
        self.ax_metrics.set_xlim(0, 1.0)
        self.ax_metrics.set_title("Signal Intensity Panel")
        self.ax_metrics.grid(axis="x", color="#28425e", alpha=0.35, linestyle=":")

    def _update_info_panel(self, snapshot: MonitoringSnapshot) -> None:
        self.info_text.delete("1.0", tk.END)
        hazard_lines = [
            f"{hazard.title} | type={hazard.hazard_type.value} | severity={hazard.severity:.2f} | confidence={hazard.confidence:.2f}"
            for hazard in snapshot.hazards
        ] or ["No strong hazards detected"]
        nasa_titles = [event.get("title", "Untitled event") for event in snapshot.nasa_events[:5]]

        text = "\n".join(
            [
                APP_TITLE,
                "",
                f"Console State: {self.live_state_var.get()}",
                f"Query: {snapshot.query}",
                f"Resolved Location: {snapshot.location.display_name}",
                f"Coordinates: {snapshot.location.latitude}, {snapshot.location.longitude}",
                f"Source: {snapshot.location.source}",
                f"Enterprise Priority Score: {snapshot.analytics.executive.enterprise_priority_score:.2f}",
                f"Investment Readiness: {snapshot.analytics.executive.investment_readiness}",
                "",
                "Hazards:",
                *hazard_lines,
                "",
                "Weather:",
                f"Temperature: {snapshot.weather.get('temperature_2m')}",
                f"Wind Speed 10m: {snapshot.weather.get('wind_speed_10m')}",
                f"Wind Gusts 10m: {snapshot.weather.get('wind_gusts_10m')}",
                f"Cloud Cover: {snapshot.weather.get('cloud_cover')}",
                "",
                "Air Quality:",
                f"US AQI: {snapshot.air_quality.get('us_aqi')}",
                f"PM2.5: {snapshot.air_quality.get('pm2_5')}",
                f"PM10: {snapshot.air_quality.get('pm10')}",
                f"Dust: {snapshot.air_quality.get('dust')}",
                f"SO2: {snapshot.air_quality.get('sulphur_dioxide')}",
                "",
                f"NASA Events In Area: {len(snapshot.nasa_events)}",
                *nasa_titles,
            ]
        )
        self.info_text.insert("1.0", text)
        self._update_weather_panel(snapshot)
        self._update_health_panel(snapshot)
        self._update_science_panel(snapshot)
        self._update_forecast_panel(snapshot)
        self._update_executive_panel(snapshot)

    def _update_weather_panel(self, snapshot: MonitoringSnapshot) -> None:
        self.weather_text.delete("1.0", tk.END)
        text = "\n".join(
            [
                "Weather Station Analytics",
                "",
                f"Operational Weather Score: {self._weather_score(snapshot):.2f}",
                f"Refresh Interval: {self.interval_var.get()} seconds",
                f"Temperature 2m: {snapshot.weather.get('temperature_2m')}",
                f"Relative Humidity 2m: {snapshot.weather.get('relative_humidity_2m')}",
                f"Wind Speed 10m: {snapshot.weather.get('wind_speed_10m')}",
                f"Wind Gusts 10m: {snapshot.weather.get('wind_gusts_10m')}",
                f"Wind Direction 10m: {snapshot.weather.get('wind_direction_10m')}",
                f"Cloud Cover: {snapshot.weather.get('cloud_cover')}",
                f"Precipitation: {snapshot.weather.get('precipitation')}",
                "",
                "Use case: weather stations, regional operations, and transport readiness.",
            ]
        )
        self.weather_text.insert("1.0", text)

    def _update_health_panel(self, snapshot: MonitoringSnapshot) -> None:
        self.health_text.delete("1.0", tk.END)
        text = "\n".join(
            [
                "Public Health Analytics",
                "",
                f"Exposure Risk Score: {self._health_score(snapshot):.2f}",
                f"Advisory Level: {snapshot.analytics.health.advisory_level}",
                f"Population Exposure Estimate: {snapshot.analytics.health.estimated_population_exposure_millions:.1f}M",
                f"Detected Hazards: {len(snapshot.hazards)}",
                f"US AQI: {snapshot.air_quality.get('us_aqi')}",
                f"European AQI: {snapshot.air_quality.get('european_aqi')}",
                f"PM2.5: {snapshot.air_quality.get('pm2_5')}",
                f"PM10: {snapshot.air_quality.get('pm10')}",
                f"Ozone: {snapshot.air_quality.get('ozone')}",
                f"Nitrogen Dioxide: {snapshot.air_quality.get('nitrogen_dioxide')}",
                "",
                "Vulnerable groups:",
                *[f"- {group}" for group in snapshot.analytics.health.vulnerable_groups],
                "",
                "Use case: health agencies, exposure assessments, and respiratory advisories.",
            ]
        )
        self.health_text.insert("1.0", text)

    def _update_science_panel(self, snapshot: MonitoringSnapshot) -> None:
        self.science_text.delete("1.0", tk.END)
        event_titles = [event.get("title", "Untitled event") for event in snapshot.nasa_events[:8]]
        text = "\n".join(
            [
                "NASA-Style Scientific Analytics",
                "",
                f"Observation Utility Score: {self._science_score(snapshot):.2f}",
                f"Signal Count: {len(snapshot.signals)}",
                f"Resolved Bounding Box: {snapshot.location.bbox}",
                f"NASA Event Count: {len(snapshot.nasa_events)}",
                "",
                "Top trigger explanations:",
                *[f"- {line}" for line in snapshot.analytics.scientific.trigger_explanations[:4]],
                "",
                "Recent events:",
                *event_titles,
                "",
                "Use case: remote sensing, atmospheric science, and EO review.",
            ]
        )
        self.science_text.insert("1.0", text)

    def _update_forecast_panel(self, snapshot: MonitoringSnapshot) -> None:
        self.forecast_text.delete("1.0", tk.END)
        forecast_lines = [
            f"- {point.horizon_hours}h | spread={point.hazard_spread_score:.2f} | aq-risk={point.air_quality_risk:.2f} | confidence={point.confidence:.2f}"
            for point in snapshot.analytics.weather.forecast
        ]
        text = "\n".join(
            [
                "Forecast and Propagation",
                "",
                f"Plume Transport Risk: {snapshot.analytics.weather.plume_transport_risk:.2f}",
                f"Station Readiness: {snapshot.analytics.weather.station_readiness}",
                "",
                "Forecast windows:",
                *forecast_lines,
                "",
                "Use case: shift planning, transport coordination, and alert timing.",
            ]
        )
        self.forecast_text.insert("1.0", text)

    def _update_executive_panel(self, snapshot: MonitoringSnapshot) -> None:
        self.executive_text.delete("1.0", tk.END)
        text = "\n".join(
            [
                "Executive and Partner Value",
                "",
                f"Enterprise Priority Score: {snapshot.analytics.executive.enterprise_priority_score:.2f}",
                f"Investment Readiness: {snapshot.analytics.executive.investment_readiness}",
                "",
                "Decision summary:",
                *[f"- {line}" for line in snapshot.analytics.executive.decision_summary],
                "",
                "Unique value points:",
                *[f"- {line}" for line in snapshot.analytics.executive.unique_value_points],
            ]
        )
        self.executive_text.insert("1.0", text)

    @staticmethod
    def _read_image(data: bytes):
        return mpimg.imread(BytesIO(data), format="png")

    def _resolve_query(self) -> tuple[str, str]:
        mode = self.query_mode_var.get()
        if mode == "Continent":
            return self.continent_var.get().strip(), "auto"
        if mode == "Address":
            return self.query_var.get().strip(), "address"
        if mode == "Coordinates":
            return f"{self.latitude_var.get().strip()},{self.longitude_var.get().strip()}", "coords"
        return self.query_var.get().strip(), "auto"

    def _weather_score(self, snapshot: MonitoringSnapshot) -> float:
        wind = float(snapshot.weather.get("wind_speed_10m") or 0.0) / 80.0
        gust = float(snapshot.weather.get("wind_gusts_10m") or 0.0) / 100.0
        cloud = float(snapshot.weather.get("cloud_cover") or 0.0) / 100.0
        return min(1.0, 0.45 * wind + 0.35 * gust + 0.20 * cloud)

    def _health_score(self, snapshot: MonitoringSnapshot) -> float:
        aqi = float(snapshot.air_quality.get("us_aqi") or 0.0) / 300.0
        pm25 = float(snapshot.air_quality.get("pm2_5") or 0.0) / 150.0
        ozone = float(snapshot.air_quality.get("ozone") or 0.0) / 180.0
        return min(1.0, 0.50 * aqi + 0.30 * pm25 + 0.20 * ozone)

    def _science_score(self, snapshot: MonitoringSnapshot) -> float:
        nasa_factor = min(1.0, len(snapshot.nasa_events) / 10.0)
        confidence = (
            sum(hazard.confidence for hazard in snapshot.hazards) / len(snapshot.hazards)
            if snapshot.hazards
            else 0.0
        )
        return min(1.0, 0.55 * nasa_factor + 0.45 * confidence)

    def run(self) -> None:
        self.root.mainloop()


def launch_app() -> None:
    app = GlobalHazardIntelApp()
    app.run()
