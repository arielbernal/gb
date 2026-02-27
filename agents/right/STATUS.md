# Agent Right — Status
**Started:** 2026-02-26

## Dead Code Audit: PASSED

Audit PASSED. Left can push.

### Summary
- **het_rt_lacam**: 27 dead items removed (functions, types, declarations, data members)
- **hetpibt**: 15 dead items removed (functions, types, unused includes, dead params)
- **Python tools**: 4 files deleted (duplicates/broken), 3 files fixed (stale paths)
- **Maps/experiments**: no orphans, no empty dirs
- **All builds clean**: het_rt_lacam 14/14 tests, hetpibt 12/12 tests
- **scen.0 verified**: 9/9 goals, SOC=404

### Key Deletions
- lacam3 leftovers: ConfigHasher, manhattanDist, Path/Paths, 6 dead metric decls
- Dead operator<< chain: Vertex*, Config, HetConfig, HNode* (never streamed)
- Unused data: fleet_occupied_now/next (allocated, never read)
- Dead APIs: elapsed_ns, pointer overloads, make_goal_config, programmatic Instance ctor
- hetpibt: backtrack_and_reserve + DepNode (superseded by push_agent), TimedCell, cell_at, remove_agent, clear, to_grid_space, recalculate_costs (no-op)

### Audit Log
Full details: `agents/right/temp/audit_log.txt`
