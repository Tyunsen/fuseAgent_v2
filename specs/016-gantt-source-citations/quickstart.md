# Quickstart: Gantt Source Citations

## Local Verification

1. Run targeted backend tests for time-trace prompt guidance and trace-support conclusion labeling.
2. Run targeted frontend verification for:
   - time-mode gantt labels and date placement
   - absence of the extra secondary time card
   - action-row `参考文档来源` entry
   - right-side source drawer behavior
   - inline `[n]` citation marker rendering
3. Run:
   - `pytest tests/unit_test/service/test_agent_chat_trace_mode.py`
   - `corepack yarn lint`
   - `corepack yarn build`

## Remote Verification

1. Sync changed backend/frontend files and regenerate `web/build`.
2. Deploy the latest code to `/home/common/jyzhu/ucml/fuseAgent-current`.
3. Restart the stack with `bash scripts/deploy-fuseagent-remote.sh`.
4. Forward ports locally and verify:
   - `http://127.0.0.1:46130/`
   - `http://127.0.0.1:46180/docs`

## Manual QA Checks

1. In a new time-mode answer for “3月发生了什么？” confirm:
   - the main graph is a gantt
   - task labels are real events
   - the graph does not collapse all items to one day when source times differ
   - no secondary card appears below the gantt
2. In any cited answer confirm:
   - the action row includes `参考文档来源`
   - clicking it opens a right-side drawer
   - the bottom source card is gone
   - the answer body contains visible `[n]` markers
   - drawer row numbering aligns with the inline markers

## Constitution Acceptance

1. Run `python scripts/run_triple_trace_acceptance.py --skip-remote-deploy`.
2. Confirm:
   - full `iw_docs` import/index completes within 4 minutes
   - collection graph page renders successfully
   - node count > 80
   - edge count > 100
   - default mode passes
   - time mode passes with corrected gantt behavior
   - space mode still passes
   - entity mode still passes
