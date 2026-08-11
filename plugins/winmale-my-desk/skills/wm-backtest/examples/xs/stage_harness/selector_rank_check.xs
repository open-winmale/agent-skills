# 最小 selector_rank 夹具：在 candidates 上排序后返回 symbol[]
xs.require("xs/simulation/test/harness.xs")

simulation.test_fixture(MAP{
  "date": "2024-06-03",
  "candidates": ARR{"000858", "600519", "000001"},
  "bars": MAP{
    "600519": MAP{"close": 1800, "volume": 1e6},
    "000858": MAP{"close": 150, "volume": 1e6},
    "000001": MAP{"close": 10, "volume": 1e6},
  },
})

# 内联最小 rank：按 close 降序取前 2
syms := bt.candidates
scored := []
for i := 0; i < LEN(syms); i++ {
  s := STRING(syms[i])
  if ! simulation.bar_ok(s, 0) {continue}
  scored = scored.append(ARR{s, bt.bar[s].close})
}
# 朴素选择排序（夹具数据很小）
for i := 0; i < LEN(scored); i++ {
  for j := i + 1; j < LEN(scored); j++ {
    if scored[j][1] > scored[i][1] {
      tmp := scored[i]
      scored[i] = scored[j]
      scored[j] = tmp
    }
  }
}
out := []
n := LEN(scored)
if n > 2 {n = 2}
for i := 0; i < n; i++ {
  out = out.append(STRING(scored[i][0]))
}
CHECK(LEN(out) == 2, "top2")
CHECK(STRING(out[0]) == "600519", "highest close first")
return MAP{"ok": true, "ranked": out}
