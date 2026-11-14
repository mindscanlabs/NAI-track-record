#!/bin/sh
# Sources of the fifth suite (fnet/README.md 25) -> D:/Claude/nai-data/fnet/fifth/raw, with the repositories' metadata
# (for their checksums) and SHA-256 of every file. Run once; files present are kept.
#     sh fnet/stand/fifth_fetch.sh
R=D:/Claude/nai-data/fnet/fifth/raw
mkdir -p $R && cd $R || exit 1
get() {   # get FILE URL
    [ -s "$1" ] || curl -sS -L --retry 5 --retry-delay 10 --max-time 1800 -o "$1" "$2" || echo "FAILED $1"
}
# metadata
get zenodo_19450971.json https://zenodo.org/api/records/19450971
get zenodo_23954638.json https://zenodo.org/api/records/23954638
get zenodo_6514897.json https://zenodo.org/api/records/6514897
get mendeley_247pvf6whn.json https://data.mendeley.com/public-api/datasets/247pvf6whn
get mendeley_zcm29bp7yf.json https://data.mendeley.com/public-api/datasets/zcm29bp7yf
get figshare_3759315.json https://api.figshare.com/v2/articles/3759315
get hf_ahmedml.json https://huggingface.co/api/datasets/neashton/ahmedml
# data
get ahmedml_geo_parameters_all.csv https://huggingface.co/datasets/neashton/ahmedml/resolve/main/geo_parameters_all.csv
get ahmedml_force_mom_all.csv https://huggingface.co/datasets/neashton/ahmedml/resolve/main/force_mom_all.csv
get lsf_wall.xlsx https://data.mendeley.com/public-files/datasets/247pvf6whn/files/4f27d405-d8be-431b-9c38-4c5184197199/file_downloaded
get curing_didearot_flatpanel_db.csv "https://zenodo.org/records/19450971/files/didearot_flatpanel_db.csv?download=1"
get cellular_beams_CBR.csv https://data.mendeley.com/public-files/datasets/zcm29bp7yf/files/fea70c40-76e2-41d4-9bc8-a26684b7e8b6/file_downloaded
get hts_superox_all_data.xlsx https://ndownloader.figshare.com/files/11274950
get tss_TSS_DATASET_v1.csv "https://zenodo.org/records/23954638/files/TSS_DATASET_v1.csv?download=1"
get lpbf_v1.1.xlsx "https://zenodo.org/records/6514897/files/Process%20Parameters%20and%20Properties%20LPBF%20v1.1.xlsx?download=1"
sha256sum *.csv *.xlsx > SHA256SUMS
cat SHA256SUMS
