"""Paths and small helpers shared by the stand scripts (fnet/README.md, step 2: P0)."""
import hashlib
import json
import os
import time
import urllib.request

DATA = os.environ.get("FNET_DATA", "D:/Claude/nai-data/fnet")
RAW = os.path.join(DATA, "raw")
META = os.path.join(DATA, "meta")
TABLES = os.path.join(DATA, "tables")
SPLITS = os.path.join(DATA, "splits")
RESULTS = os.path.join(DATA, "results")
# Small files that define the experiment live in the repository.
REPO_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def download(url, path, tries=4):
    """Download to path (via a .part file); skip when path exists."""
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "nai-fnet-stand"})
            with urllib.request.urlopen(req, timeout=300) as r, open(path + ".part", "wb") as f:
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    f.write(b)
            os.replace(path + ".part", path)
            return
        except Exception as e:
            print(f"  retry {k + 1}: {url}: {e}")
            time.sleep(5 * (k + 1))
    raise RuntimeError(f"download failed: {url}")


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "nai-fnet-stand"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def metrics(y, p, fallback):
    """R² (by the test's own spread), RMSE and the count of non-finite predictions, which are replaced by
    fallback (the training mean)."""
    import numpy as np
    p = np.asarray(p, dtype=float)
    ok = np.isfinite(p)
    p = np.where(ok, p, fallback)
    ss = np.sum((y - y.mean()) ** 2)
    r2 = 1 - np.sum((y - p) ** 2) / ss if ss > 0 else np.nan
    return r2, float(np.sqrt(np.mean((y - p) ** 2))), int((~ok).sum())


def load_splits(fn):
    """A table's split arrays and their info, with the lower-tail splits of <fn>.lo.* merged in if present."""
    import json
    import numpy as np
    arrays = dict(np.load(os.path.join(SPLITS, fn + ".npz")))
    info = json.load(open(os.path.join(SPLITS, fn + ".json")))
    lo = os.path.join(SPLITS, fn + ".lo.npz")
    if os.path.exists(lo):
        arrays.update(dict(np.load(lo)))
        info.update(json.load(open(os.path.join(SPLITS, fn + ".lo.json"))))
    return arrays, info
