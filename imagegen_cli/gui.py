from __future__ import annotations

import queue
from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6 import QtCore, QtGui, QtWidgets

from .filter_manifest import FilterDefinition, ParameterDefinition, load_manifest
from .history import load_metadata
from .job_runner import ImageJobRunner, JobEvent


class ParameterEditor(QtWidgets.QWidget):
    def __init__(self, parameter: ParameterDefinition) -> None:
        super().__init__()
        self.parameter = parameter
        self._layout = QtWidgets.QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self.label = QtWidgets.QLabel(parameter.name)
        self.label.setMinimumWidth(120)
        self._layout.addWidget(self.label)

        self.input = self._build_input(parameter)
        self._layout.addWidget(self.input)

    def _build_input(self, parameter: ParameterDefinition) -> QtWidgets.QWidget:
        if parameter.type == "int":
            box = QtWidgets.QSpinBox()
            if parameter.min is not None:
                box.setMinimum(int(parameter.min))
            if parameter.max is not None:
                box.setMaximum(int(parameter.max))
            if parameter.step is not None:
                box.setSingleStep(int(parameter.step))
            if parameter.default is not None:
                box.setValue(int(parameter.default))
            return box
        if parameter.type == "float":
            box = QtWidgets.QDoubleSpinBox()
            if parameter.min is not None:
                box.setMinimum(float(parameter.min))
            if parameter.max is not None:
                box.setMaximum(float(parameter.max))
            if parameter.step is not None:
                box.setSingleStep(float(parameter.step))
            if parameter.default is not None:
                box.setValue(float(parameter.default))
            return box
        if parameter.type == "bool":
            chk = QtWidgets.QCheckBox()
            chk.setChecked(bool(parameter.default))
            return chk
        if parameter.type == "enum":
            combo = QtWidgets.QComboBox()
            for item in parameter.enum or []:
                combo.addItem(item)
            if parameter.default is not None:
                idx = combo.findText(str(parameter.default))
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            return combo

        line = QtWidgets.QLineEdit()
        if parameter.default is not None:
            line.setText(str(parameter.default))
        return line

    def value(self) -> Any:
        widget = self.input
        if isinstance(widget, QtWidgets.QSpinBox):
            return widget.value()
        if isinstance(widget, QtWidgets.QDoubleSpinBox):
            return widget.value()
        if isinstance(widget, QtWidgets.QCheckBox):
            return widget.isChecked()
        if isinstance(widget, QtWidgets.QComboBox):
            return widget.currentText()
        if isinstance(widget, QtWidgets.QLineEdit):
            return widget.text()
        return None


class ImageGenWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ImageGen Local GUI")
        self.resize(900, 700)

        self.manifest = load_manifest()
        self._events: queue.Queue[JobEvent] = queue.Queue()
        self._runner: ImageJobRunner | None = None
        self._parameter_editors: dict[str, ParameterEditor] = {}
        self._history_records: list[Path] = []

        root = QtWidgets.QWidget()
        self.setCentralWidget(root)
        layout = QtWidgets.QVBoxLayout(root)

        self.filter_select = QtWidgets.QComboBox()
        for f in self.manifest.filters:
            self.filter_select.addItem(f"{f.name} ({f.id})", userData=f.id)
        self.filter_select.currentIndexChanged.connect(self._render_parameter_controls)
        layout.addWidget(self.filter_select)

        self.param_container = QtWidgets.QWidget()
        self.param_layout = QtWidgets.QVBoxLayout(self.param_container)
        layout.addWidget(self.param_container)

        button_bar = QtWidgets.QHBoxLayout()
        self.generate_btn = QtWidgets.QPushButton("Generate")
        self.generate_btn.clicked.connect(self._start_generation)
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._cancel_generation)
        self.cancel_btn.setEnabled(False)
        button_bar.addWidget(self.generate_btn)
        button_bar.addWidget(self.cancel_btn)
        layout.addLayout(button_bar)

        self.progress = QtWidgets.QProgressBar()
        layout.addWidget(self.progress)

        self.status_log = QtWidgets.QPlainTextEdit()
        self.status_log.setReadOnly(True)
        self.status_log.setMaximumBlockCount(800)
        layout.addWidget(self.status_log)

        history_group = QtWidgets.QGroupBox("History")
        history_layout = QtWidgets.QVBoxLayout(history_group)
        history_buttons = QtWidgets.QHBoxLayout()
        self.history_path = QtWidgets.QLineEdit()
        self.history_path.setPlaceholderText("Output directory with sidecar metadata JSON files")
        self.history_reload = QtWidgets.QPushButton("Load")
        self.history_reload.clicked.connect(self._load_history)
        history_buttons.addWidget(self.history_path)
        history_buttons.addWidget(self.history_reload)
        history_layout.addLayout(history_buttons)
        self.history_list = QtWidgets.QListWidget()
        self.history_list.itemSelectionChanged.connect(self._apply_history_item)
        history_layout.addWidget(self.history_list)
        layout.addWidget(history_group)

        self.preview_label = QtWidgets.QLabel("Preview will appear here")
        self.preview_label.setMinimumHeight(320)
        self.preview_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("border: 1px solid #666; background: #111; color: #ddd;")
        layout.addWidget(self.preview_label)

        self._poll_timer = QtCore.QTimer(self)
        self._poll_timer.timeout.connect(self._drain_events)
        self._poll_timer.start(100)

        self._render_parameter_controls()

    def _current_filter(self) -> FilterDefinition:
        filter_id = str(self.filter_select.currentData())
        selected = self.manifest.by_id(filter_id)
        if not selected:
            raise RuntimeError("No filter selected")
        return selected

    def _render_parameter_controls(self) -> None:
        while self.param_layout.count():
            child = self.param_layout.takeAt(0)
            if child and child.widget():
                child.widget().deleteLater()

        self._parameter_editors.clear()
        filter_def = self._current_filter()
        for param in filter_def.parameters:
            editor = ParameterEditor(param)
            self._parameter_editors[param.name] = editor
            self.param_layout.addWidget(editor)

        if "output_dir" in self._parameter_editors and not self.history_path.text():
            self.history_path.setText(str(self._parameter_editors["output_dir"].value()))

    def _append_log(self, text: str) -> None:
        self.status_log.appendPlainText(text)

    def _set_preview_image(self, path: Path) -> None:
        pixmap = QtGui.QPixmap(str(path))
        if pixmap.isNull():
            self.preview_label.setText(f"Could not load image: {path}")
            return
        scaled = pixmap.scaled(
            self.preview_label.width(),
            self.preview_label.height(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        current = self.preview_label.pixmap()
        if current:
            self.preview_label.setPixmap(
                current.scaled(
                    self.preview_label.width(),
                    self.preview_label.height(),
                    QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                    QtCore.Qt.TransformationMode.SmoothTransformation,
                )
            )

    def _start_generation(self) -> None:
        if self._runner and self._runner.is_alive():
            self._append_log("job already running")
            return

        values = {name: editor.value() for name, editor in self._parameter_editors.items()}
        filter_def = self._current_filter()

        self.progress.setValue(0)
        self._append_log(f"starting job for filter={filter_def.id} values={values}")
        self.generate_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)

        self._runner = ImageJobRunner(filter_def, values, self._events)
        self._runner.start()

    def _load_history(self) -> None:
        source_dir = Path(self.history_path.text() or self._parameter_editors["output_dir"].value()).expanduser().resolve()
        if not source_dir.exists():
            self._append_log(f"history path does not exist: {source_dir}")
            return

        metadata_files = sorted(source_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        self.history_list.clear()
        self._history_records = []
        for path in metadata_files:
            try:
                data = load_metadata(path)
            except Exception:  # noqa: BLE001
                continue
            timestamp = str(data.get("timestamp", "unknown"))
            filter_id = str(data.get("filter_id", "unknown"))
            try:
                parsed = datetime.fromisoformat(timestamp)
                timestamp = parsed.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
            item = QtWidgets.QListWidgetItem(f"{timestamp} — {filter_id} — {path.name}")
            item.setToolTip(str(path))
            self.history_list.addItem(item)
            self._history_records.append(path)

        self._append_log(f"loaded {len(self._history_records)} history records from {source_dir}")

    def _apply_history_item(self) -> None:
        index = self.history_list.currentRow()
        if index < 0 or index >= len(self._history_records):
            return
        path = self._history_records[index]
        try:
            metadata = load_metadata(path)
        except Exception as exc:  # noqa: BLE001
            self._append_log(f"failed to read history metadata {path}: {exc}")
            return

        filter_id = str(metadata.get("filter_id", ""))
        filter_index = self.filter_select.findData(filter_id)
        if filter_index >= 0:
            self.filter_select.setCurrentIndex(filter_index)

        values = metadata.get("resolved_parameters", {})
        if isinstance(values, dict):
            for name, editor in self._parameter_editors.items():
                if name not in values:
                    continue
                value = values[name]
                widget = editor.input
                if isinstance(widget, QtWidgets.QSpinBox):
                    widget.setValue(int(value))
                elif isinstance(widget, QtWidgets.QDoubleSpinBox):
                    widget.setValue(float(value))
                elif isinstance(widget, QtWidgets.QCheckBox):
                    widget.setChecked(bool(value))
                elif isinstance(widget, QtWidgets.QComboBox):
                    idx = widget.findText(str(value))
                    if idx >= 0:
                        widget.setCurrentIndex(idx)
                elif isinstance(widget, QtWidgets.QLineEdit):
                    widget.setText(str(value))

        self._append_log(f"loaded history record: {path}")

    def _cancel_generation(self) -> None:
        if self._runner and self._runner.is_alive():
            self._append_log("cancel requested")
            self._runner.cancel()

    def _drain_events(self) -> None:
        while True:
            try:
                event = self._events.get_nowait()
            except queue.Empty:
                break

            self._append_log(f"[{event.kind}] {event.message}")
            if event.progress is not None:
                self.progress.setValue(max(0, min(100, event.progress)))
            if event.image_path is not None:
                self._set_preview_image(event.image_path)
            if event.metadata_path is not None:
                self._append_log(f"metadata sidecar: {event.metadata_path}")
                current_output_dir = str(self._parameter_editors["output_dir"].value())
                self.history_path.setText(current_output_dir)
                self._load_history()
            if event.kind in {"done", "error", "canceled"}:
                self.generate_btn.setEnabled(True)
                self.cancel_btn.setEnabled(False)


def run_gui() -> int:
    app = QtWidgets.QApplication([])
    window = ImageGenWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run_gui())
