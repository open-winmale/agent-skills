# 官方示例：目标权重一次性建仓（无再平衡）
# from_universe / from_strategy / from_watchlist 不接受 weights
# 自定义权重必须 run_custom 挂本脚本（先 preview_custom）
# BUY wt = 占可用现金比例，不是金额（元）
# 必须 return append_order 累积的列表；禁止 return 字符串 / ECHO

xs.require("xs/simulation/lib/init.xs")

# 按代码对齐权重（合计建议 ≤ 1）。未出现在候选池里的代码会被跳过。
syms := ["600519", "000858", "600887"]
wts := [0.20, 0.18, 0.15]

nav := book.nav
cash := book.cash
if nav <= 0 || cash <= 0 {
  return nil
}

# 已有持仓 → 买入持有，不再交易
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

out := []
for i := 0; i < LEN(syms); i++ {
  sym := STRING(syms[i])
  wt := FLOAT(wts[i])
  if wt <= 0 {
    continue
  }
  in_pool := false
  for j := 0; j < LEN(pool); j++ {
    if STRING(pool[j]) == sym {
      in_pool = true
      break
    }
  }
  if ! in_pool {
    continue
  }
  if ! simulation.bar_ok(sym, 1000) {
    continue
  }
  out = simulation.append_order(out, sym, "BUY", wt, "target_weight")
}
if LEN(out) == 0 {
  return nil
}
return out
