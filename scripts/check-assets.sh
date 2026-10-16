#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

fail() { printf 'Asset check failed: %s\n' "$1" >&2; exit 1; }

for n in $(seq 1 60); do
  printf -v id '%03d' "$n"
  test -s "Code/listing_${id}.txt" || fail "missing or empty Code/listing_${id}.txt"
done

for chapter in 1 2 3 5 6; do
  case "$chapter" in
    1) last=2 ;; 2) last=1 ;; 3) last=5 ;; 5) last=11 ;; 6) last=5 ;;
  esac
  for number in $(seq 1 "$last"); do
    test -s "Equations/equation_${chapter}_${number}.tex" || fail "missing equation ${chapter}.${number}"
  done
done

for dir in cph1 cph2 cph3 cph4 cph5 cph6; do
  test -d "imgs/$dir" || fail "missing imgs/$dir"
done

for name in fig_technique_catalogue fig_evidence_ladder fig_blind_vs_evidence_retry fig_maker_checker fig_knowledge_triad fig_parallel_control fig_safety_router fig_capstone_orchestra fig_selection_tree_final fig_support_resolution_loop; do
  test -s "imgs/cph6/${name}.png" || fail "missing chapter 6 figure ${name}.png"
done

printf 'Asset inventory OK: 60 listings, 24 equations, 6 chapter figure directories, 10 chapter 6 figures.\n'
