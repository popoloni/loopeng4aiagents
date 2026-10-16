# Chapter 6: Choosing the Right Loop

The chapter's listings are compact teaching adaptations, not copies of the [measured course notebooks](https://github.com/FareedKhan-dev/agentic-loop-engineering-course). The [standalone script](../src/loop_engineering.py) turns these fragments into callable, tested mechanisms and a bounded code-repair CLI. The CLI composes the core generate/check/feedback/escalate path; the other patterns are callable building blocks, not automatically executed by that CLI. Use the original course for experimental methods and results, not this offline demo. The model adapter uses the course's local vLLM chat-completions protocol; the default retrieval and triage scorer uses standard-library lexical similarity, so it does not reproduce BGE results.

| Mechanism | Book listing |
| --- | --- |
| Bounded retry with executable feedback | [042](../Code/listing_042.txt) |
| Maker and independent checker | [043](../Code/listing_043.txt) |
| Context from schema and examples | [044](../Code/listing_044.txt) |
| Retrieval-backed memory | [045](../Code/listing_045.txt) |
| Tool-grounded code execution | [046](../Code/listing_046.txt) |
| Isolated Git work and integration | [047](../Code/listing_047.txt) |
| Multi-loop ownership and priority | [048](../Code/listing_048.txt) |
| Token budget projection | [049](../Code/listing_049.txt) |
| Conservative auto-act guardrail | [050](../Code/listing_050.txt) |
| Protected verifier assets | [051](../Code/listing_051.txt) |
| Semantic triage | [052](../Code/listing_052.txt) |
| CI failure versus flake classification | [053](../Code/listing_053.txt) |
| Dependency-update routing | [054](../Code/listing_054.txt) |
| Additional production patterns: duplicate issues, PRs, debt, changelog | [055](../Code/listing_055.txt) |
| Staged orchestration | [056](../Code/listing_056.txt) |
| Minimal loop contract | [057](../Code/listing_057.txt) |
| Technology-neutral task contract | [058](../Code/listing_058.txt) |
| Minimum sufficient control selection | [059](../Code/listing_059.txt) |
| Customer-support resolution loop | [060](../Code/listing_060.txt) |

The matching figures are in [`imgs/cph6/`](../imgs/cph6/) and the chapter's equation fragments are [`equation_6_1.tex`](../Equations/equation_6_1.tex) through [`equation_6_5.tex`](../Equations/equation_6_5.tex). The labels in this table describe each snippet's role; they do not certify it as executable software.

The script keeps Git integration and external actions as explicit function calls; the CLI only verifies candidate code and reports or escalates. It tests all 19 listing groups with [unit tests](../tests/test_loop_engineering.py). A timeout limits how long a subprocess runs, but does **not** prevent filesystem or network access by candidate code. Only run trusted code in the offline JSON mode, and use an isolated host when opting into generated code.
