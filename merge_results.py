"""Merge Run 1B and Run 2B forex results into RESULTS.md."""
import json
from pathlib import Path

SRC = Path(__file__).parent
results_path = SRC / "RESULTS.md"

# Load saved results
with open(SRC / "forex_run1b_results.json") as f:
    run1b = json.load(f)
with open(SRC / "forex_ltf_compare.json") as f:
    ltf_compare = json.load(f)

with open(results_path, "r", encoding="utf-8") as f:
    content = f.read()

# ===== 1. Add forex rows to Run 1 table =====
# Find the Run 1 table end (empty line before ## Run 2)
run1_end = content.find("\n## Run 2")
if run1_end > 0:
    # Find the blank line just before "## Run 2"
    insert_point = content.rfind("\n", 0, run1_end) + 1
    
    forex_rows = []
    for r in run1b:
        forex_rows.append(f"| {r['pair']:<8} | {r['config']:<8} | {r['trades']:<5} | {r['win_rate']:<5.1f}% | ${r['pnl']:<+8.2f} | {r['pf']:<5.2f} | {r['dd']:<5.1f}% | {r['sharpe']:<7.2f} | ${r['avg_win']:<7.2f} | ${r['avg_loss']:<7.2f} |")
    
    forex_block = "\n" + "\n".join(forex_rows) + "\n"
    content = content[:insert_point] + forex_block + content[insert_point:]

# ===== 2. Add forex LTF=ON rows to Run 2 table =====
run2_table_header = "| pair | config | ltf | trades | win_rate | pnl | pf | dd | sharpe |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
run2_start = content.find(run2_table_header)
if run2_start > 0:
    # Find end of Run 2 table (line before "### LTF Impact Summary" or blank line before next section)
    ltf_impact_start = content.find("### LTF Impact Summary", run2_start)
    if ltf_impact_start > 0:
        # The table ends at the blank line before LTF Impact Summary
        table_end = content.rfind("\n\n", run2_start, ltf_impact_start) + 1
        
        # Add forex LTF=ON rows
        on_rows = []
        for r in ltf_compare:
            if r["ltf"] == "LTF=ON":
                on_rows.append(f"| {r['pair']:<8} | {r['config']:<8} | {r['ltf']:<8} | {r['trades']:<5} | {r['win_rate']:<5.1f}% | ${r['pnl']:<+8.2f} | {r['pf']:<5.2f} | {r['dd']:<5.1f}% | {r['sharpe']:<7.2f} |")
        
        on_block = "\n" + "\n".join(on_rows) + "\n"
        content = content[:table_end] + on_block + content[table_end:]

# ===== 3. Clean up LTF Impact Summary (remove incorrect forex rows, add proper ones) =====
impact_section_start = content.find("### LTF Impact Summary")
if impact_section_start > 0:
    next_section = content.find("\n## ", impact_section_start + 5)
    if next_section < 0:
        next_section = len(content)
    
    # Remove everything between the impact table header line and the next section
    # The impact table header is: "| Pair | Config | LTF=OFF PnL | LTF=ON PnL | Delta | Trades OFF | Trades ON |"
    impact_header = content.find("| Pair | Config | LTF=OFF PnL", impact_section_start)
    if impact_header > 0:
        # Find the actual start of the table (the header line)
        table_start_line = content.rfind("\n", 0, impact_header) + 1
        
        # Remove all existing impact rows (from table_start_line to next_section)
        content = content[:table_start_line] + "\n" + content[next_section:]
    
    # Build impact map from crypto (already in content) and forex ltf_compare data
    # First, extract crypto entries that are already correct in the section
    # Actually, let me just rebuild the entire impact section
    
    # Find the header line again
    impact_header = content.find("| Pair | Config | LTF=OFF PnL", impact_section_start)
    if impact_header > 0:
        # Find the table body start (after the separator line)
        sep_line_end = content.find("\n", content.find("\n| ---", impact_header)) + 1
        
        # Build impact rows from scratch
        impact_rows = []
        
        # Crypto impact rows (hardcoded from correct existing data)
        crypto_impact = [
            ("BTC/USDT", "Base", "$+91198.47", "$+22563.33", "$-68635.15", "1374", "594"),
            ("BTC/USDT", "C3_OFF", "$+127131.43", "$+24389.51", "$-102741.91", "1528", "632"),
            ("BTC/USDT", "KZ_ON", "$+5544.82", "$+7396.19", "$+1851.37", "411", "180"),
            ("BTC/USDT", "M1_Only", "$+617.69", "$+1949.40", "$+1331.71", "570", "262"),
            ("ETH/USDT", "Base", "$+66266.26", "$+8707.37", "$-57558.89", "1360", "595"),
            ("ETH/USDT", "C3_OFF", "$+55435.34", "$+7538.77", "$-47896.57", "1515", "652"),
            ("ETH/USDT", "KZ_ON", "$+4018.07", "$+2948.48", "$-1069.59", "408", "187"),
            ("ETH/USDT", "M1_Only", "$+2321.71", "$+776.97", "$-1544.75", "550", "239"),
            ("SOL/USDT", "Base", "$+239087.58", "$+28714.09", "$-210373.49", "1477", "449"),
            ("SOL/USDT", "C3_OFF", "$+562432.93", "$+36111.42", "$-526321.51", "1689", "488"),
            ("SOL/USDT", "KZ_ON", "$+24635.63", "$+10502.58", "$-14133.04", "433", "137"),
            ("SOL/USDT", "M1_Only", "$+11597.36", "$+7180.61", "$-4416.75", "629", "201"),
        ]
        
        for p, c, off_pnl, on_pnl, delta, off_t, on_t in crypto_impact:
            impact_rows.append(f"| {p} | {c} | {off_pnl} | {on_pnl} | {delta} | {off_t} | {on_t} |")
        
        # Forex impact rows from ltf_compare data
        ltf_map = {}
        for r in ltf_compare:
            k = (r["pair"], r["config"])
            ltf_map.setdefault(k, {})[r["ltf"]] = r
        
        for (p, c), modes in sorted(ltf_map.items()):
            off = modes.get("LTF=OFF")
            on = modes.get("LTF=ON")
            if off and on:
                d = on["pnl"] - off["pnl"]
                impact_rows.append(f"| {p} | {c} | ${off['pnl']:+.2f} | ${on['pnl']:+.2f} | ${d:+.2f} | {off['trades']:.0f} | {on['trades']:.0f} |")
        
        impact_block = "\n".join(impact_rows) + "\n"
        content = content[:sep_line_end] + impact_block + content[sep_line_end:]

# ===== 4. Add forex best configs to the summary tables =====
# "Best Config Per Pair"
best_config_start = content.find("### Best Config Per Pair")
if best_config_start > 0:
    best_config_end = content.find("### Best", best_config_start + 5)
    if best_config_end > 0:
        # Find the end of the table
        table_end = content.rfind("\n", 0, best_config_end)
        
        # Build forex best configs (from LTF=ON Run 1B - worst case since LTF=ON underperforms)
        # Actually, let's just add the best from Run 1B (LTF=ON) but note they're LTF=ON
        best_map = {}
        for r in run1b:
            p = r["pair"]
            if p not in best_map or r["pnl"] > best_map[p]["pnl"]:
                best_map[p] = r
        
        forex_best = []
        for p in ["EUR/USD", "GBP/USD", "XAU/USD", "XAG/USD"]:
            r = best_map.get(p)
            if r:
                forex_best.append(f"| {r['pair']:<8} | {r['config']:<8} | {r['trades']:<5} | {r['win_rate']:<5.1f}% | ${r['pnl']:<+8.2f} | {r['pf']:<5.2f} | {r['dd']:<5.1f}% | {r['sharpe']:<7.2f} |")
        
        if forex_best:
            forex_best_block = "\n" + "\n".join(forex_best) + "\n"
            content = content[:table_end] + forex_best_block + content[table_end:]

with open(results_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Updated {results_path}", flush=True)
