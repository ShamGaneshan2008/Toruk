| Variant / inference | NLL seeds | Correct | Unsupported unknown | Wrong nonempty | Train s | Inference s | Forward positions |
|---|---:|---:|---:|---:|---:|---:|---:|
| memory_off/full | 0.5318/0.5300 | 14/96 | 12 | 82 | 12.68 | 0.910 | 23762 |
| memory_on/full | 0.5198/0.5220 | 17/96 | 12 | 79 | 23.10 | 1.667 | 23453 |
| memory_on/no_read | 0.5618/0.5595 | 11/96 | 15 | 85 | 23.10 | 1.406 | 29375 |
| memory_on/no_update | 0.5635/0.5614 | 12/96 | 15 | 84 | 23.10 | 1.773 | 29278 |
| ordinary/full | 0.5318/0.5300 | 14/96 | 12 | 82 | 12.94 | 0.790 | 23762 |
| ordinary/rolling | 0.5318/0.5300 | 4/96 | 16 | 92 | 12.94 | 0.573 | 25280 |
| ordinary_matched/full | 0.4973/0.4998 | 15/96 | 11 | 81 | 13.26 | 0.843 | 23630 |
| ordinary_matched/rolling | 0.4973/0.4998 | 0/96 | 16 | 96 | 13.26 | 0.888 | 37888 |
