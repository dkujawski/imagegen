from __future__ import annotations

import os
import queue
import signal
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .filter_manifest import FilterDefinition


@dataclass
class JobEvent:
    kind: str
    message: str
    progress: int | None = None
    image_path: Path | None = None


class ImageJobRunner(threading.Thread):
    def __init__(self, filter_def: FilterDefinition, values: dict[str, Any], events: "queue.Queue[JobEvent]") -> None:
        super().__init__(daemon=True)
        self.filter_def = filter_def
        self.values = values
        self.events = events
        self._cancel = threading.Event()
        self._current_process: subprocess.Popen[str] | None = None
        self._preview_path: Path | None = None

    def cancel(self) -> None:
        self._cancel.set()
        self._terminate_process_group()

    def _emit(self, kind: str, message: str, progress: int | None = None, image_path: Path | None = None) -> None:
        self.events.put(JobEvent(kind=kind, message=message, progress=progress, image_path=image_path))

    def _terminate_process_group(self) -> None:
        if self._current_process and self._current_process.poll() is None:
            try:
                os.killpg(self._current_process.pid, signal.SIGTERM)
            except ProcessLookupError:
                return

    def _run_script(self, size: int, output_dir: Path, file_name: str, stage: str) -> Path:
        script = Path(__file__).resolve().parents[1] / self.filter_def.script_path
        cmd = [str(script), str(size), str(output_dir), file_name]
        self._emit("status", f"[{stage}] running: {' '.join(cmd)}")
        self._current_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        assert self._current_process.stdout
        for line in self._current_process.stdout:
            self._emit("log", f"[{stage}] {line.strip()}")

        code = self._current_process.wait()
        self._current_process = None
        if code != 0:
            if self._cancel.is_set() and code in {-15, 143}:
                raise InterruptedError(f"job canceled during {stage} render")
            raise RuntimeError(f"{stage} render failed with exit code {code}")

        output_path = output_dir / f"{file_name}.png"
        if not output_path.exists():
            raise RuntimeError(f"{stage} render did not create expected output: {output_path}")

        return output_path

    def _cleanup_preview(self) -> None:
        if self._preview_path and self._preview_path.exists():
            self._preview_path.unlink(missing_ok=True)

    def run(self) -> None:
        try:
            size = int(self.values["size"])
            output_dir = Path(self.values["output_dir"]).expanduser().resolve()
            output_dir.mkdir(parents=True, exist_ok=True)
            file_name = str(self.values["file_name"])
            max_preview = int(self.filter_def.output.get("preview_safe_limits", {}).get("max_size", 512))
            preview_size = min(size, max_preview)

            self._emit("status", "starting preview render", progress=5)
            if self._cancel.is_set():
                raise InterruptedError("job canceled before start")

            preview_dir = Path(tempfile.mkdtemp(prefix="imagegen-preview-"))
            preview_file_name = f"{file_name}_preview_{int(time.time())}"
            self._preview_path = self._run_script(preview_size, preview_dir, preview_file_name, "preview")
            self._emit("preview", "preview ready", progress=55, image_path=self._preview_path)

            if self._cancel.is_set():
                raise InterruptedError("job canceled after preview")

            self._emit("status", "starting full render", progress=60)
            final_path = self._run_script(size, output_dir, file_name, "full")
            self._emit("done", f"render complete: {final_path}", progress=100, image_path=final_path)
        except InterruptedError as exc:
            self._cleanup_preview()
            self._emit("canceled", str(exc), progress=0)
        except Exception as exc:  # noqa: BLE001
            self._emit("error", str(exc), progress=0)
