# 用夹具跑 pe_filter 风格止盈：持仓浮盈≥10% 应产出 SELL take_profit
xs.require("xs/simulation/test/harness.xs")

simulation.test_fixture(MAP{
  "date": "2024-06-03",
  "cash": 200000,
  "nav": 1000000,
  "candidates": ARR{"000858"},
  "params": MAP{"take_profit_pct": 0.10, "max_pe": 15, "max_pos_pct": 0.1, "max_buy_wt": 0.05},
  "bars": MAP{
    "600519": MAP{"close": 1800, "volume": 1e6},
    "000858": MAP{"close": 150, "volume": 1e6},
  },
  "positions": MAP{
    "600519": MAP{"quantity": 100, "avg_cost": 1500, "last_price": 1800},
  },
})

# 内联与 examples/xs/pe_filter/trading.xs 同构的持仓止盈段
tp := simulation.tuning("take_profit_pct", 0.10)
out := []
held := simulation.held_symbols()
for i := 0; i < LEN(held); i++ {
  sym := STRING(held[i])
  px := 0.0
  if simulation.bar_ok(sym, 0) {
    px = bt.bar[sym].close
  } else if HAS(book.positions, sym) {
    px = FLOAT(DEFAULT(book.positions[sym].last_price, 0))
  }
  qty := simulation.position_qty(sym)
  if qty <= 0 || px <= 0 {continue}
  cost := simulation.position_cost(sym)
  if cost > 0 {
    pnl := px / cost - 1
    if pnl >= tp {
      simulation.rule("take_profit")
      out = simulation.append_order(out, sym, "SELL", 1.0, "take_profit")
    }
  }
}
CHECK(LEN(out) == 1, "one take_profit order")
CHECK(STRING(out[0][0]) == "600519", "sym")
CHECK(STRING(out[0][1]) == "SELL", "side")
CHECK(STRING(out[0][4]) == "take_profit", "reason")
CHECK(DEFAULT(bt.rule_counts.take_profit, 0) >= 1, "rule counted")
return MAP{"ok": true, "orders": out}
