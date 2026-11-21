# DSH requirement-change study

This synthetic software study asks whether an explicit decision record helps an agent recover from a requirement change. Both arms use the same DSH runtime, model, tool boundary, and behavior checks. The record arm writes its own dependency record and receives the affected decision IDs when the controller sends the change.

Protocol 4.1 changes the pagination contract after a working core checkpoint. Protocol 4.2 (`local-export`) first verifies a working live list and batch export, then changes only export. The revised export traverses the rows present at its first call. The live list still pages through current rows with integer offsets. Three checks cover the live path and four cover export, including concurrent traversals and JSON cursor round-trips.

The controller uses DSH's native steering at a tool boundary and verifies that the change enters the next step of the same turn. Tool execution and code checks run in separate restricted Linux containers. The behavior checks are designed for this non-adversarial study. See [the runtime bridge](runtime/README.md) for the event sequence and [results.json](results.json) for the reduced observations.

## Observed comparisons

| Protocol | Arm | Independent checks | Seconds | Output tokens | Total recorded tokens |
| --- | --- | ---: | ---: | ---: | ---: |
| 4.1, pagination | native | 9/9 | 64.48 | 9,441 | 56,055 |
| 4.1, pagination | dependency_record | 9/9 | 89.20 | 12,571 | 83,128 |
| 4.2, local export | native | 7/7 | 84.79 | 13,649 | 63,407 |
| 4.2, local export | dependency_record | 7/7 | 128.97 | 19,786 | 144,823 |

Each row above is one valid trial. The record arm took 24.73 seconds longer in 4.1 and 44.17 seconds longer in 4.2. Both arms in the valid 4.2 pair modified only the export API and tests among the code and test files. The record arm additionally updated its record. It flagged all five decisions for review, including the preserved live path. Those flags did not manifest as live regressions.

In a second local-export run the record arm passed. Native failed the v1 checkpoint before steering: it exposed a string cursor while the oracle expected an integer offset. The initial prompt specifies the integer offset for the shared paginator and leaves the outward export cursor type implicit. Its final-phase checks are diagnostic and this attempt cannot support a comparison of responses to the revised requirement. The archived metrics also retain the earlier 4.0 attempts.

The valid comparisons give no evidence to make decision records the default for these small tasks. We retained the mechanism as a traceability option. These samples do not establish general equivalence or effectiveness. Elapsed time includes teardown and excludes preflight and final evaluation. Total recorded tokens include cache reads and are not a cost estimate.

## Run locally

Use Python 3.11 and Node.js. From the repository root:

```sh
cd research/dsh-lab
python3.11 -m venv .venv-dsh
.venv-dsh/bin/python -m pip install -r requirements.txt
npm ci --prefix npm-runtime
./change-study/run-local.sh --offline-check
```

The offline suite includes steering probes against the installed DSH loop with a fake model. For a live trial, use a host with access to a Linux Docker daemon. Run `./change-study/run-local.sh --prepare-image` to pull the Python image and verify the isolation checks ahead of the API call. Set `DEEPSEEK_API_KEY` in a private `research/dsh-lab/.env` file, then run:

```sh
./change-study/run-local.sh --scenario local-export
```

This starts one sequential pair with the default limit of 8,192 output tokens per model request. The runner performs isolation and bridge preflight before loading API credentials. It writes per-arm results and the paired summary under `change-study/runs/`. Live trials use the DeepSeek API. Use `--preflight-only` to verify a prepared host without a model call.
