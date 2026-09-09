# Put this project on GitHub — 4 commands in Terminal on the Mac

`tfi_hackathon.bundle` in this folder holds the complete repository (285 files, one commit).
The `.git` folder currently here is broken (created from the sandbox, which is not allowed to delete files), so step 1 removes it.

1. Create an empty repository on github.com — https://github.com/new — named `tfi_hackathon`, Private, **no** README / .gitignore / licence.

2. In Terminal:

```
cd ~/Desktop/aiOS/tfi_hackathon
rm -rf .git tfi_hackathon.bundle.part00 tfi_hackathon.bundle.part01 repo_snapshot.tgz project_sync.tgz
git clone --bare tfi_hackathon.bundle .git && git config --unset core.bare && git reset --hard
git remote add origin https://github.com/eliasmocik/tfi_hackathon.git && git push -u origin main
```

`git status` afterwards should be clean — the large data files are covered by `.gitignore`.

## For teammates

```
git clone https://github.com/eliasmocik/tfi_hackathon.git
cd tfi_hackathon/participant-kit && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

Read `README.md`, then `project/MASTER.md` (the specification everything follows).

## What is deliberately not in git

Raw SEM-O pulls (BM-037, BM-096, BM-101), the ENTSO-E 2022 zips, the synthetic weather years, the WP2024 wind-in network, and the large `.parquet` result tables. They are regenerable and the READMEs say how: `data/README.md` (SEM-O API), `data/synth_out_extra/README.md` (synthetic years and the wind-in network), `project/MASTER.md` §11 (re-running the engine). Keep them in your local folder; `.gitignore` already hides them.

## Why this was not pushed from Claude

The GitHub connection gives this session read access to repositories it is configured for; it cannot create a repository or authenticate a `git push`. Creating the empty repo yourself and running the four commands above is the whole difference.
