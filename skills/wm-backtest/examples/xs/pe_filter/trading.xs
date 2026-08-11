xs.require("xs/simulation/lib/init.xs")
max_pe := simulation.tuning("max_pe", 15)
max_pos := simulation.tuning("max_pos_pct", 0.10)
max_buy := simulation.tuning("max_buy_wt", 0.05)
tp := simulation.tuning("take_profit_pct", 0.10)
nav := book.nav
cash := book.cash
if nav <= 0 {return nil}
out := []
held := simulation.held_symbols()
for i := 0; i < LEN(held); i++ {
  sym := STRING(held[i])
  # 持仓监控：simulation.bar / last_price（PIT 补价；勿猜 pos.price）
  px := simulation.last_price(sym)
  qty := simulation.position_qty(sym)
  if qty <= 0 || px <= 0 {continue}
  cost := simulation.position_cost(sym)
  if cost > 0 {
    pnl := px / cost - 1
    if pnl >= tp {
      simulation.rule("take_profit")
      out = simulation.append_order(out, sym, "SELL", 1.0, "take_profit")
      continue
    }
  }
}
pool := bt.candidates
if LEN(pool) == 0 {pool = bt.universe}
for i := 0; i < LEN(pool); i++ {
  sym := STRING(pool[i])
  if simulation.position_qty(sym) > 0 {continue}
  if ! simulation.bar_ok(sym, 1000) {continue}
  pe := simulation.pe_ttm(sym)
  if pe <= 0 || pe >= max_pe {continue}
  w := max_buy
  if w > max_pos {w = max_pos}
  if cash <= 0 {break}
  simulation.rule("pe_entry")
  out = simulation.append_order(out, sym, "BUY", w, "pe_entry")
  simulation.trace("trading", "XS_TRACE", "pe_entry", {"sym": sym, "pe": pe, "w": w})
}
if LEN(out) == 0 {return nil}
return out
