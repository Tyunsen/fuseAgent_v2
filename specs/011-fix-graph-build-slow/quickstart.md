# Quickstart: MiroFish Graph Start Latency Recovery

## 1. Run targeted unit tests

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit_test/mirofish_graph/test_document_service_graph_queue.py tests/unit_test/mirofish_graph/test_mirofish_graph_service.py
```

Expected result:

- Immediate-start scheduling tests pass
- Existing stale-revision and incremental-update tests continue to pass

## 2. Start the verification stack

Preferred when validating on the approved remote server:

```bash
ssh jyzhu@211.87.232.112
cd /home/common/jyzhu/ucml/fuseAgent-current
docker compose ps
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:36180/docs
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:36130/
```

Local fallback:

```powershell
docker compose up -d
```

Fallback when running services directly:

```powershell
make run-backend
make run-celery
```

Expected result:

- Backend API is reachable
- Celery worker is running and can receive collection graph tasks

## 3. Prepare a smoke dataset from `iw_docs`

Suggested first pass:

- Use `E:\codes\fuseAgent_v2\iw_docs\01.md`
- Use `E:\codes\fuseAgent_v2\iw_docs\02.md`
- Use one larger file such as `E:\codes\fuseAgent_v2\iw_docs\news_source_01_chinanews.md`

## 4. Smoke-test a new MiroFish collection

1. Create a new MiroFish knowledge base.
2. Upload and confirm the selected `iw_docs` files.
3. Observe backend/Celery logs and the collection graph lifecycle immediately
   after confirmation.

Expected result:

- The graph task is submitted immediately after confirmation, with no built-in
  10-second idle wait before task submission.
- The graph lifecycle moves into active processing promptly.
- Total graph completion may still take longer than vector/fulltext, which is
  acceptable and distinct from start latency.

## 5. Rapid-confirm safety check

1. Add another document quickly after the first confirmation.
2. Confirm it before the previous graph work fully settles.

Expected result:

- A newer revision is prepared immediately.
- Outdated work remains skippable by the current freshness logic.
- Active-graph availability is preserved.

## Observed Result (2026-04-02)

- Targeted unit validation passed with:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit_test/mirofish_graph/test_document_service_graph_queue.py tests/unit_test/mirofish_graph/test_mirofish_graph_service.py
```

- Result: `20 passed`
- Remote stack validation was completed successfully on `211.87.232.112` under `/home/common/jyzhu/ucml/fuseAgent-current`.
- Remote service reachability was healthy during validation:
  - `http://127.0.0.1:36180/docs` returned `200`
  - `http://127.0.0.1:36130/` returned `200`
  - `docker ps` showed `aperag-api`, `aperag-celeryworker`, and `aperag-frontend` running
- A new collection was created successfully with payload:

```json
{"title":"Graph Start Test <timestamp>","description":"remote timing validation"}
```

- The API auto-filled `type` as `document`; sending uppercase `DOCUMENT` is what triggers `collection type is not supported`.
- Smoke documents sourced from `E:\codes\fuseAgent_v2\iw_docs` and mirrored on the server as `/home/common/jyzhu/ucml/iw_docs_test` were uploaded and confirmed:
  - `01.md`
  - `02.md`
  - `news_source_01_chinanews.md`
- Confirm request time on the server: `2026-04-02T17:50:36+08:00`
- API log immediately after confirm:

```text
2026-04-02 09:50:36,899 - INFO - Queue MiroFish graph build for collection col38b495f188879292 at revision 1 with immediate start
```

- Celery worker received the collection graph task immediately after that:

```text
2026-04-02 09:50:36,905 celery.worker.strategy - Task config.celery_tasks.mirofish_collection_graph_task[...] received
```

- Six seconds after confirm, collection state had already moved from `waiting_for_documents` to:
  - `graph_status = building`
  - `graph_revision = 1`
- Document status snapshots after confirm showed the graph index had already entered active creation instead of waiting:
  - `graph_index_status = CREATING`
  - vector/fulltext were also running in parallel
- Conclusion: the fixed 10-second built-in queue delay is gone on the remote stack. The graph index now starts immediately after document confirmation. Any remaining slowness is build-time work inside graph extraction/indexing, not delayed task submission.
