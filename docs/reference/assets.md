# Asset guide

This repository retains its original publisher-facing filenames so existing references and download instructions do not silently break. The organization is by **asset type**, with the chapter map below providing the reading order.

| Folder | Contents | Convention |
| --- | --- | --- |
| [`Code/`](../../Code/) | 60 illustrative listings | `listing_001.txt` through `listing_060.txt`, numbered in book order |
| [`Equations/`](../../Equations/) | 24 LaTeX equation fragments | `equation_<chapter>_<number>.tex` |
| [`imgs/`](../../imgs/) | Chapter figures and other image assets | Historical `cph*` directory labels; see mapping below |

| Book chapter | Figure directory | Listings | Equations |
| --- | --- | --- | --- |
| 1 — Foundations | [`imgs/cph1/`](../../imgs/cph1/) | `listing_001` | `equation_1_1`–`1_2` |
| 2 — Organization | [`imgs/cph3/`](../../imgs/cph3/) | — | `equation_2_1` |
| 3 — Economics | [`imgs/cph4/`](../../imgs/cph4/) | — | `equation_3_1`–`3_5` |
| 4 — Ralph loop | [`imgs/cph2/`](../../imgs/cph2/) | `listing_002`–`019` | — |
| 5 — Local AI loop | [`imgs/cph5/`](../../imgs/cph5/) | `listing_020`–`041` | `equation_5_1`–`5_11` |
| 6 — Choosing the right loop | [`imgs/cph6/`](../../imgs/cph6/) | `listing_042`–`060` | `equation_6_1`–`6_5` |

The `cph*` figure labels are historical and **do not consistently match chapter numbers**. In particular, chapter 6 manuscript source refers to `imgs/chapter06/`, but the released files are in [`imgs/cph6/`](../../imgs/cph6/). Use the latter path in this repository. This guide records the discrepancy without renaming assets that existing readers or publisher workflows may reference.

[`imgs/cover.jpg`](../../imgs/cover.jpg), [`imgs/author-photo.png`](../../imgs/author-photo.png), and [`imgs/series_qr.PNG`](../../imgs/series_qr.PNG) are cover or front/back-matter assets, not chapter figures.

## Reading code listings

Numbered `.txt` files preserve the text as printed. They intentionally do not imply a shared language or executable entry point. For example, chapter 4 has prompts and shell fragments; chapter 5 includes configuration and setup examples; chapter 6 includes compact Python adaptations of control mechanisms. Do not run a listing merely because its contents look like a command. Consult the book's surrounding explanation, replace placeholders, and review any action that touches credentials, repositories, or services.
