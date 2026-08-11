# 最小 risk 夹具：无 bar 的提案应被丢弃
xs.require("xs/simulation/test/harness.xs")

simulation.test_fixture(MAP{
  "date": "2024-06-03",
  "cash": 200000,
  "nav": 1000000,
  "bars": MAP{
    "600519": MAP{"close": 1800, "volume": 1e6},
  },
  "proposals": ARR{
    ARR{"600519", "BUY", 0.05, 0, "entry"},
    ARR{"999999", "BUY", 0.05, 0, "no_bar"},
  },
})

# 与 examples/xs/pe_filter/risk.xs 同构
out := []
for i := 0; i < LEN(bt.proposals); i++ {
  p := bt.proposals[i]
  sym := STRING(p[0])
  if ! simulation.bar_ok(sym, 0) {continue}
  out = out.append(p)
}
CHECK(LEN(out) == 1, "drop missing bar")
CHECK(STRING(out[0][0]) == "600519", "kept traded name")
return MAP{"ok": true, "orders": out}
