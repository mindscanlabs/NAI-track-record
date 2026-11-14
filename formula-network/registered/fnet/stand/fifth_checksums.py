"""Checksums of the fifth suite's sources against the repositories' metadata (fifth_fetch.sh): Zenodo and figshare
give md5, Mendeley sha256; Hugging Face gives the files' git object ids (sha1 of 'blob <size>\\0' + content) or LFS
sha256. Prints one line per file.
    python -s -E fifth_checksums.py
"""
import hashlib
import json
import os

R = "D:/Claude/nai-data/fnet/fifth/raw"
FILES = {   # local file: (metadata file, the file's name in the repository)
    "curing_didearot_flatpanel_db.csv": ("zenodo_19450971.json", "didearot_flatpanel_db.csv"),
    "tss_TSS_DATASET_v1.csv": ("zenodo_23954638.json", "TSS_DATASET_v1.csv"),
    "lpbf_v1.1.xlsx": ("zenodo_6514897.json", "Process Parameters and Properties LPBF v1.1.xlsx"),
    "lsf_wall.xlsx": ("mendeley_247pvf6whn.json", "COMSOL_based_LSF_wall_thermal_dataset.xlsx"),
    "cellular_beams_CBR.csv": ("mendeley_zcm29bp7yf.json", "CBR.csv"),
    "hts_superox_all_data.xlsx": ("figshare_3759315.json", "All data.xlsx"),
    "ahmedml_geo_parameters_all.csv": ("hf_ahmedml.json", "geo_parameters_all.csv"),
    "ahmedml_force_mom_all.csv": ("hf_ahmedml.json", "force_mom_all.csv"),
}


def digest(path, name):
    h = hashlib.new(name)
    h.update(open(path, "rb").read())
    return h.hexdigest()


def main():
    for local, (meta, name) in FILES.items():
        path = os.path.join(R, local)
        m = json.load(open(os.path.join(R, meta), encoding="utf-8"))
        want, kind = None, None
        if meta.startswith("zenodo"):
            f = next(f for f in m["files"] if f["key"] == name)
            kind, want = "md5", f["checksum"].split(":", 1)[1]
        elif meta.startswith("figshare"):
            f = next(f for f in m["files"] if f["name"] == name)
            kind, want = "md5", f["computed_md5"]
        elif meta.startswith("mendeley"):
            f = next(f for f in m["files"] if f["filename"] == name)
            kind, want = "sha256", f["content_details"]["sha256_hash"]
        else:
            f = next(f for f in m["siblings"] if f["rfilename"] == name)
            if "lfs" in f:
                kind, want = "sha256", f["lfs"]["sha256"]
            else:
                data = open(path, "rb").read()
                got = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
                print(f"{local:36s} git-sha1 {'OK' if got == f.get('blobId', got) else 'DIFFERS'} "
                      f"({'blobId given' if 'blobId' in f else 'no blobId in metadata'})")
                continue
        got = digest(path, kind)
        print(f"{local:36s} {kind} {'OK' if got == want else 'DIFFERS: ' + got + ' vs ' + str(want)}")


if __name__ == "__main__":
    main()
