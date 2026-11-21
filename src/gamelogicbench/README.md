# GameLogicBench Harbor Adapter

## Overview

**Draft.** The candidate release covers 51 headless controller tasks and 1,055 scenario/seed cells. Final validation and publication permission are pending. See [the historical acceptance findings](validation/acceptance.md).

Build private Harbor task directories from pinned local GameLogicBench checkouts. The adapter source contains the generator and integration code. It does not distribute upstream games, judges or reference solutions.

## What is GameLogicBench?

GameLogicBench evaluates gameplay logic in Godot 4.4 projects. An agent edits the project, then a deterministic judge runs the submission across public and hidden scenarios. The pinned upstream snapshot contains 72 tasks and 1,474 scenario/seed cells. The paper reports 1,451 cells. The reason for the count difference has not been confirmed.

## Adapter Features

- One stable Harbor task per supported original task ID. Full and parity generation use the same conversion path.
- The agent receives the upstream brief and playable project. The verifier runs the frozen judge and the submitted controller under separate users and processes.
- Oracle installs the upstream `proper` overlay into the editable project and goes through the normal artifact and verifier path. Use `--reference naive` in a separate local directory for negative calibration.
- Headless validation uses the pinned Godot 4.4 runtime. The manifest preserves Press arguments, per-seed resource settings and declared delivery paths.
- The runtime selects the official Godot AMD64 or ARM64 archive for the Docker build platform and verifies its pinned checksum. Tasks with the upstream native GDExtension pin the game and verifier services to AMD64; other tasks and Harbor's sidecar can run natively on ARM64.

## Generated Task Structure

```text
<output>/<original_task_id>/
  task.toml
  instruction.md
  environment/Dockerfile
  environment/game/
  solution/solve.sh
  solution/reference/
  tests/Dockerfile
  tests/test.sh
  tests/verify.py
  tests/private/{task.yaml,evaluation.json,game/,judge/}
```

## Run Evaluation / Harness

The registry entry is pending. [Historical validation evidence](validation/README.md) covers the earlier 72-task implementation. Newly generated tasks include the runtime build in their Dockerfiles and can run on a clean Docker backend.

```bash
harbor trial start -p ../../datasets/gamelogicbench-poc/atom_active_frames -a oracle
harbor run -c run_gamelogicbench.yaml
```

The bundled run config targets the full generated dataset. It starts two concurrent trials and uses sequential seed evaluation within each verifier.

## Usage: Create Task Directories

Run from the adapter directory. Set the paths to the pinned upstream repositories first.

```bash
uv run gamelogicbench --harness-dir "$GLB_HARNESS" --tasks-dir "$GLB_TASKS" \
  --output-dir ../../datasets/gamelogicbench-poc \
  --task-ids atom_active_frames combo_reverse_dock repo_watch_rotation

uv run gamelogicbench --harness-dir "$GLB_HARNESS" --tasks-dir "$GLB_TASKS" \
  --output-dir ../../datasets/gamelogicbench
```

Use `--limit N` to select a sorted prefix and `--overwrite` to regenerate tasks in place. To avoid mixing subsets, use a clean output directory for each independent run. Generated folders are kept private. Do not attach them to a PR or publish them to an image registry before permission is confirmed.

## Comparison with Original Benchmark (Parity)

The historical provisional cohort contains three paired runs on 24 tasks (8 atom / 8 combo / 8 repo, 472 cells per run). Scores are mean ± sample SEM; all per-kind and overall run-score ranges overlap. The Harbor cohort mixes driver revisions, so these observations are not final frozen-configuration parity confirmation.

All seven historical whole-task disagreement pairs were cross-graded in the opposite evaluator: **14 submissions, 294/294 matching cell verdicts**. These replays describe the historical cohort. See [acceptance findings](validation/acceptance.md) and [cross-grade evidence](validation/crossgrade-disagreements.json).

The pilot is excluded. Model-budget timeouts are retained and judged; four unusable attempts are archived and replaced. Counting the oversized-tool-argument attempt's original zero leaves the reported aggregate unchanged. See the linked reproduction notes for the complete policy and driver history.

| Agent | Model | Metric | Number of Runs | Dataset Size | Original Performance | Harbor Performance |
| --- | --- | --- | ---: | ---: | --- | --- |
| codex@0.144.1 | gpt-5-mini | Task pass rate (%) | 3 per side | 24/72 (33.3%) | 13.8889 ± 2.7778 | 18.0556 ± 3.6747 |

See [per-run and per-task summaries](validation/parity-results.json), [the fixed task list](parity_task_ids.txt), and [both-side reproduction and methodology](validation/parity-reproduction.md). Local Colima Linux was used; Daytona was not used.

To replay the historical cohort, use the archived 72-task adapter and runtime
described in the reproduction guide. Run both sides with a fresh result directory
for each round. The candidate release requires a new subset drawn from its
supported tasks.

```bash
harbor run -c run_gamelogicbench_parity.yaml --job-name run-1

python -m geb.cli command=run "task=[$(paste -sd, "$GLB_PARITY_TASK_IDS")]" \
  solution=gpt-5-mini scaffold=codex effort=high \
  image=gamelogicbench-parity:codex-0.144.1 \
  solve.concurrency=2 judge.concurrency=2 sample_num=1 result_dir=parity-original-run-1
```

## Notes & Caveats

- The upstream harness starts a container per seed. The adapter starts one separate verifier container per trial and isolates sequential seed executions inside it. Check the target backend's isolation and egress policy before using the adapter with models.
- The candidate excludes 18 project-module tasks, one rendered task, and two tasks requiring live game-object mutation. See [the task-level exclusions](excluded_tasks.json).
- The verifier supervisor writes the task reward using the trusted judge's results. Missing or unusable judge results produce an explicit infrastructure failure.
- Verifier logs include Godot diagnostics and a private `cells.jsonl` with every scenario/seed verdict. Keep these detailed logs private; publish only reviewed summaries and terminal screenshots.
- Source checkouts must match the fixed SHAs below and have clean tracked files. Generation copies Git-tracked assets only.
- Publication requires upstream permission for the GameLogicBench materials and compliance with the vendored upstream project licenses.
- Confirm the task registry namespace and contributor contact through the v2 review workflow.

## Installation / Prerequisites

Use Python 3.11+, uv, Git, and a Linux Docker backend with the pinned Harbor release or checkout. The current adapter specification describes Harbor baseline `99218a4611e3bd76e49ce3b5f977e8c8134ad3ac`.

```bash
git clone https://github.com/NJU-LINK/GameLogicBench.git
git -C GameLogicBench fetch origin 10287322040bc72574f144cb40eccfd6ccb66936
git -C GameLogicBench checkout --detach 10287322040bc72574f144cb40eccfd6ccb66936
git clone https://github.com/NJU-LINK/GameLogicBench-Tasks.git
git -C GameLogicBench-Tasks checkout --detach 82f51ab34860c0ab3fe63a0ce9ae394ad38234a6

uv sync --locked
```

Set `GLB_HARNESS` and `GLB_TASKS` to the respective absolute paths. The runtime Dockerfile pins the base image and checks the exact Godot version and archive checksum. Use `--runtime-image` to target an equivalent prebuilt image accessible from a different backend.

## Troubleshooting

- If generation rejects a checkout, verify its head, root and tracked status.
- If a task built with `--runtime-image` cannot resolve the image, regenerate without the override or use an image reachable from the Docker backend.
- For a failed Oracle, compare the generated verifier log with the separately evaluated upstream `proper` solution. Start with `atom_move_navigation` to isolate headless operation.
- Confirm the Linux Docker backend supports separate verification, no-network execution and the egress sidecar’s required kernel features for allowlists.

## Citation

```bibtex
@article{che2026gamelogicbench,
  title = {GameLogicBench: Evaluating Coding Agents on Runtime Game Logic with Tick-Level State Assertions},
  author = {Che, Xinyu and Ge, Yunfei and Li, Shihao and Liu, Yanchen and Yan, Hang and Lei, Xinping and Wang, Yanghai and Dong, Zixuan and Yao, Yifan and Xie, Qianqian and Zhu, Letian and Liu, Jiaheng},
  journal = {arXiv preprint arXiv:2609.21562},
  year = {2026}
}
```

## Authors & Contributions

The benchmark is by Xinyu Che and colleagues at NJU-LINK. The Harbor adapter was prepared by ShawVentus with Codex.
