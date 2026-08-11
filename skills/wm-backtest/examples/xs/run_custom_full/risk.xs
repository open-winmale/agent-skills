xs.require("xs/simulation/lib/init.xs")
min_day_vol := simulation.tuning("min_day_vol", 1000.0)
if LEN(bt.proposals) == 0 {
  return nil
}
out := []
for i := 0; i < LEN(bt.proposals); i++ {
  p := bt.proposals[i]
  sym := STRING(p[0])
  side := STRING(p[1])
  if !simulation.bar_ok(sym, min_day_vol) {
    continue
  }
  SETCURSORXS(sym)
  if side == "BUY" && $IS_ST {
    continue
  }
  out = out.append(p)
}
if LEN(out) == 0 {
  return nil
}
return out
