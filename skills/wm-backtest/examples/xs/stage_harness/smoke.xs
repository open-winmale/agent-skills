# stage harness smoke — 持仓不在 candidates 仍可取价/成本
xs.require("xs/simulation/test/harness.xs")

meta := simulation.test_fixture_held_out_of_pool()
CHECK(meta.positions_n == 1, "one position")
CHECK(LEN(bt.candidates) == 1, "one candidate")
CHECK(!simulation.sym_in_list("600519", bt.candidates), "held out of pool")
CHECK(simulation.bar_ok("600519", 0), "held has bar")
px := bt.bar["600519"].close
cost := simulation.position_cost("600519")
CHECK(px == 1800, "close")
CHECK(cost == 1500, "avg_cost")
pnl := px / cost - 1
CHECK(pnl > 0.1, "take-profit would fire")
diag := simulation.bar_diag("999999")
CHECK(diag.ok == false, "missing bar")
return MAP{"ok": true, "pnl": pnl, "meta": meta}
