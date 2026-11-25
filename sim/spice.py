"""
Run LTspice in batch mode and read its .raw output. No dependencies beyond numpy.

LTSPICE env var overrides the executable path.
"""
import os
import re
import subprocess
from pathlib import Path

import numpy as np

LTSPICE = os.environ.get(
    "LTSPICE", str(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/ADI/LTspice/LTspice.exe"))


def read_raw(path):
    """Transient .raw (binary, single run) -> {'time': array, 'v(vbus)': array, ...}."""
    b = Path(path).read_bytes()
    marker = "Binary:\n".encode("utf-16le")
    i = b.index(marker)
    hdr = b[:i].decode("utf-16le")
    data = b[i + len(marker):]
    nvar = int(re.search(r"No\. Variables:\s*(\d+)", hdr)[1])
    npts = int(re.search(r"No\. Points:\s*(\d+)", hdr)[1])
    names = re.findall(r"^\s*\d+\s+(\S+)\s+\S+\s*$", hdr.split("Variables:")[-1], re.M)
    assert len(names) == nvar, (len(names), nvar)
    flags = re.search(r"Flags:(.*)", hdr)[1]
    if "double" in flags:
        a = np.frombuffer(data, "<f8", count=npts * nvar).reshape(npts, nvar)
        cols = [a[:, k] for k in range(nvar)]
    else:  # time is float64, everything else float32
        rec = np.frombuffer(data, np.dtype([("t", "<f8"), ("v", "<f4", (nvar - 1,))]), count=npts)
        cols = [rec["t"]] + [rec["v"][:, k].astype(float) for k in range(nvar - 1)]
    out = {n.lower(): c for n, c in zip(names, cols)}
    out["time"] = np.abs(out["time"])  # LTspice uses the sign bit as a flag
    return out


def run(cir_path, timeout=3600):
    """Run one netlist, return its waveforms. Raises with the log tail on failure."""
    cir_path = Path(cir_path).resolve()
    raw, log = cir_path.with_suffix(".raw"), cir_path.with_suffix(".log")
    raw.unlink(missing_ok=True)
    subprocess.run([LTSPICE, "-b", str(cir_path)], timeout=timeout, check=False)
    if not raw.exists():
        text = log.read_bytes().decode("utf-16le", "ignore") if log.exists() else "(no log)"
        raise RuntimeError(f"{cir_path.name}: no .raw produced\n{text[-2000:]}")
    return read_raw(raw)


def log_text(cir_path):
    log = Path(cir_path).with_suffix(".log")
    b = log.read_bytes()
    return b.decode("utf-16le", "ignore") if b[1:2] == b"\0" else b.decode("latin1")


if __name__ == "__main__":
    # self-check: a tiny RC netlist, compare against the analytic answer
    import tempfile
    d = Path(tempfile.mkdtemp())
    (d / "rc.cir").write_text("* rc\nV1 in 0 PWL(0 0 1n 1)\nR1 in out 1k\nC1 out 0 1u\n"
                              ".tran 0 5m 0 1u\n.save V(out)\n.end\n")
    w = run(d / "rc.cir")
    t, v = w["time"], w["v(out)"]
    k = np.searchsorted(t, 1e-3)
    assert abs(v[k] - (1 - np.exp(-t[k] / 1e-3))) < 0.01, v[k]
    print("spice.py self-check OK:", len(t), "points")
