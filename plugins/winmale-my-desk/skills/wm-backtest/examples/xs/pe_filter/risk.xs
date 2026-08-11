xs.require("xs/simulation/lib/init.xs")
if LEN(bt.proposals) == 0 {return nil}
out := []
for i := 0; i < LEN(bt.proposals); i++ {
  p := bt.proposals[i]
  sym := STRING(p[0])
  if ! simulation.bar_ok(sym, 0) {continue}
  out = out.append(p)
}
return out
