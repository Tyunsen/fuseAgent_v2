# Quickstart: MiroFish Build Speed Recovery

1. Restart the remote stack in `/home/common/jyzhu/ucml/fuseAgent-current`.
2. Forward the remote web and API ports to local ports.
3. Run:

   ```powershell
   $env:FUSEAGENT_REMOTE_SSH_PASSWORD="<server-password>"
   python scripts/run_triple_trace_acceptance.py
   ```

4. Verify the acceptance report shows:
   - a fresh collection created from all files in `E:\codes\fuseAgent_v2\iw_docs`
   - vector, fulltext, and graph indexing finished within 4 minutes
   - collection graph node count > 80
   - collection graph edge count > 100
   - default, time, space, and entity mode validations all passed
5. If the run fails, use the structured failure reasons plus remote service logs to isolate the slowest phase or broken contract.
