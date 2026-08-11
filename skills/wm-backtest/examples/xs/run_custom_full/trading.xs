xs.require("xs/simulation/lib/init.xs")
invest_pct := simulation.tuning("invest_pct", 0.95)
min_day_vol := simulation.tuning("min_day_vol", 1000.0)
nav := book.nav
cash := book.cash
if nav <= 0 || cash <= 0 {
  return nil
}
held := simulation.held_symbols()
if LEN(held) > 0 {
  return nil
}
pool := bt.candidates
if LEN(pool) == 0 {
  pool = bt.universe
}
if LEN(pool) == 0 {
  return nil
}
syms := []
for i := 0; i < LEN(pool); i++ {
  sym := STRING(pool[i])
  if simulation.bar_ok(sym, min_day_vol) {
    syms = syms.append(sym)
  }
}
n := LEN(syms)
if n == 0 {
  return nil
}
w := invest_pct / FLOAT(n)
out := []
for i := 0; i < n; i++ {
  out = simulation.append_order(out, STRING(syms[i]), "BUY", w, "ew_custom")
}
return out
