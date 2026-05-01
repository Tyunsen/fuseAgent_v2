# Quickstart: Trace Graph Citations

## Local Verification

1. Run targeted backend checks:
   - `pytest tests/unit_test/service/test_agent_chat_trace_mode.py`
   - `pytest tests/unit_test/answer_graph/test_trace_support_service.py`
   - `pytest tests/unit_test/answer_graph/test_answer_graph_service.py`
2. Run frontend checks in `web/`:
   - `corepack yarn lint`
   - `corepack yarn build`
3. Confirm locally that:
   - the answer header no longer renders a detached citation-number strip
   - inline `[n]` markers appear in cited prose
   - entity mode still uses the knowledge-graph renderer
   - time mode still uses a gantt main graph

## Remote Verification

1. Sync changed source files and regenerated `web/build` to `/home/common/jyzhu/ucml/fuseAgent-current`.
2. Restart the remote stack with `bash scripts/deploy-fuseagent-remote.sh`.
3. Recreate local forwarding to:
   - `http://127.0.0.1:46130/`
   - `http://127.0.0.1:46180/docs`
4. Use fresh chat messages, not old history, to verify:
   - default mode still behaves like the current baseline
   - time mode renders a readable gantt with real event labels and differentiated dates
   - inline `[n]` markers are clickable
   - clicking `[n]` opens and focuses the right-side `参考文档来源` drawer
   - entity mode renders a non-empty answer-scoped knowledge subgraph for graph-ready `@知识库` queries

## Constitution Acceptance

1. Import the full acceptance dataset from `E:\codes\fuseAgent_v2\iw_docs`.
2. Run `python scripts/run_triple_trace_acceptance.py --skip-remote-deploy`.
3. Confirm:
   - vector + fulltext + graph indexing completes within 4 minutes
   - the collection graph page renders successfully
   - graph node count is greater than 80
   - graph edge count is greater than 100
   - default mode returns text + inline citations + topology flow + drawer entry
   - time mode returns text + inline citations + gantt main graph + drawer entry
   - space mode remains shell-compatible with default mode
   - entity mode returns text + inline citations + non-empty knowledge subgraph + drawer entry
