# copilot_v2 arm — train+val results index

Recorded 2026-07-11/12. Engine: omni-copilot CLI (shipped pipeline: pr-review@5
4-lens ensemble / issue-answer@2, dry-run posting), DeepSeek-routed LLM per .env.
Per-item isolated RUN_ROOT (see run_copilot_arm.py header for the collision bug
this works around). 30/30 items; blocked (exit 3, safe-abstain) = issue4960, issue4992, issue5003.

**Totals**: ~$3.27 (DeepSeek est.) · 9.2M in / 724k out tokens · 107 min agent-wall

| split | item | rc | usd | min | in_tok | out_tok |
|---|---|---|---|---|---|---|
| val | issue4793 | 0 | 0.04 | 2.7 | 110,633 | 8,571 |
| val | issue4827 | 0 | 0.02 | 1.0 | 69,954 | 3,587 |
| val | issue4842 | 0 | 0.02 | 1.4 | 51,226 | 2,874 |
| val | issue4891 | 0 | 0.04 | 1.7 | 117,033 | 5,171 |
| val | issue4905 | 0 | 0.02 | 1.6 | 44,515 | 6,815 |
| val | pr4810 | 0 | 0.25 | 4.8 | 756,255 | 46,100 |
| val | pr4816 | 0 | 0.25 | 2.8 | 813,474 | 30,109 |
| val | pr4825 | 0 | 0.09 | 2.4 | 235,669 | 24,670 |
| val | pr4837 | 0 | 0.18 | 5.0 | 447,078 | 51,161 |
| val | pr4893 | 0 | 0.11 | 5.2 | 229,844 | 43,287 |
| train | issue4806 | 0 | 0.01 | 1.1 | 36,757 | 3,298 |
| train | issue4814 | 0 | 0.05 | 1.8 | 150,290 | 5,195 |
| train | issue4840 | 0 | 0.07 | 2.8 | 233,051 | 5,578 |
| train | issue4940 | 0 | 0.01 | 1.0 | 38,500 | 3,935 |
| train | issue4952 | 0 | 0.02 | 1.4 | 46,041 | 3,977 |
| train | issue4960 | 3 | 0.03 | 1.8 | 99,388 | 4,773 |
| train | issue4966 | 0 | 0.03 | 2.0 | 81,472 | 4,693 |
| train | issue4992 | 3 | 0.02 | 1.5 | 53,502 | 4,394 |
| train | issue5003 | 3 | 0.06 | 3.1 | 183,512 | 12,629 |
| train | issue5023 | 0 | 0.05 | 2.0 | 154,622 | 6,215 |
| train | pr4804 | 0 | 0.31 | 6.4 | 967,600 | 48,366 |
| train | pr4817 | 0 | 0.10 | 5.1 | 172,686 | 46,656 |
| train | pr4859 | 0 | 0.25 | 7.3 | 699,981 | 54,807 |
| train | pr4870 | 0 | 0.32 | 5.3 | 993,320 | 48,625 |
| train | pr4923 | 0 | 0.15 | 6.5 | 364,937 | 51,002 |
| train | pr4926 | 0 | 0.12 | 6.5 | 256,343 | 49,640 |
| train | pr4950 | 0 | 0.14 | 4.6 | 365,740 | 35,888 |
| train | pr4970 | 0 | 0.24 | 3.5 | 759,799 | 27,223 |
| train | pr4977 | 0 | 0.09 | 4.5 | 166,099 | 37,274 |
| train | pr5009 | 0 | 0.18 | 7.2 | 463,532 | 47,497 |
