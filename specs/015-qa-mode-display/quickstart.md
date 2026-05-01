# Quickstart: QA Mode Display

## Local Verification

1. Run targeted backend tests covering chat mode guidance and answer shell cleanup.
2. Run targeted frontend verification for:
   - inline references
   - collapsed source list
   - time/default/space/entity graph selection
   - document-level graph status visibility
   - 15-second polling stop/start behavior
3. Run:
   - `python -m compileall aperag/service/trace_answer_service.py`
   - `corepack yarn lint`
   - `corepack yarn build`

## Remote Verification

1. Deploy the latest code to `/home/common/jyzhu/ucml/fuseAgent-current`.
2. Start the remote stack with `bash scripts/deploy-fuseagent-remote.sh`.
3. Forward ports to local and verify:
   - `http://127.0.0.1:46130/`
   - `http://127.0.0.1:46180/docs`

## Constitution Acceptance

1. Run `python scripts/run_triple_trace_acceptance.py`.
2. Confirm:
   - full `iw_docs` import/index completes within 4 minutes
   - collection graph page renders successfully
   - node count > 80
   - edge count > 100
   - default mode passes
   - time mode passes
   - space mode passes under the new default-shell + `graph TD` contract
   - entity mode passes with knowledge-graph rendering

## Manual UX Checks

1. In chat:
   - answer text streams progressively
   - inline citations are visible
   - only one collapsed source list is shown
   - default/time/space/entity modes do not show duplicate summary/conclusion/source cards
2. In documents page for a MiroFish collection:
   - each document shows graph status
   - the page refreshes every 15 seconds during active graph build
   - refresh stops after build completion
