# naturaljustice.csv vs CouncilsAuditData2025.csv diff

- Councils in naturaljustice (2024/25, parseable): 78
- Councils in target:                              78
- Councils with at least one differing field:      12
- Broken rows skipped in naturaljustice.csv:       0

## Scope and matching rules

Matched on Council name, filtered to Financial year == 2024/25.
Column map (naturaljustice → target):

| naturaljustice | target |
|---|---|
| Type of audit report | Opinion type |
| Type N (qualified/EoM/…) | Type N |
| Nature of qualified opinion N / Nature of EoM N | Nature N |
| Description N | Description N |
| second 'Description 6' (header typo) | Description 7 |

Differences below are only shown when they survive these normalisations:
whitespace collapse, dashes unified to `-`, 0x19 → `'`, U+FFFD stripped,
case-insensitive match on Type/Opinion fields, and the synonym table:

  - `qualified` → `Qualified opinion`
  - `qualified opinion` → `Qualified opinion`
  - `emphasis of matter` → `Emphasis of matter paragraph`
  - `emphasis of matter paragraph` → `Emphasis of matter paragraph`
  - `key audit matter` → `Key audit matter`
  - `other matter paragraph` → `Other matter paragraph`

Empty naturaljustice values never overwrite populated target values.
Target-only columns (preserved as-is): Latitude, Longitude, Description 8.
naturaljustice-only column (ignored): Address.

## Per-council field differences

### Greater Wellington Regional Council

- **Nature 5**
  - target: `Inherent uncertainties in the measurement of greenhouse gas emissions`
  - nj:     `Greenhouse gas emissions`

### Hawke's Bay Regional Council

- **Description 7**
  - target: ``
  - nj:     `Other Matter Paragraph`
- **Type 8**
  - target: `Other matter paragraph`
  - nj:     `The Regional Council has chosen to report its greenhouse gas (GHG) emissions in its performance information. Without further modifying our opinion and considering the public interest in climate change related information, we draw attention …`

### Hutt City Council

- **Nature 5**
  - target: `Inherent uncertainties in the measurement of greenhouse gas emissions`
  - nj:     `Greenhouse gas emissions`

### Kaipara District Council

- **Description 4**
  - target: `Future of water delivery. Without modifying our opinion, we draw attention to the note on pages 159 to 160, which outlines that in response to the Government’s Local Water Done Well reforms, the Council has decided to establish a multi-owne…`
  - nj:     `Future of water delivery. Without modifying our opinion, we draw attention to Note 16 on page 73, which outlines developments in the Government’s water services reform programme. Without modifying our opinion, we draw attention to the note …`

### Nelson City Council

- **Nature 5**
  - target: `Inherent uncertainties in the measurement of greenhouse gas emissions`
  - nj:     `Greenhouse gas emissions`

### Palmerston North City Council

- **Nature 5**
  - target: `Inherent uncertainties in the measurement of greenhouse gas emissions`
  - nj:     `Greenhouse gas emissions`

### Tauranga City Council

- **Nature 5**
  - target: `Inherent uncertainties in the measurement of greenhouse gas emissions`
  - nj:     `Greenhouse gas emissions`

### Upper Hutt City Council

- **Nature 5**
  - target: `Inherent uncertainties in the measurement of greenhouse gas emissions`
  - nj:     `Greenhouse gas emissions`

### Waikato Regional Council

- **Description 4**
  - target: `Inherent uncertainties in the measurement of greenhouse gas emissions The Council has chosen to include a measure of its greenhouse gas (GHG) emissions in its performance information. Without modifying our opinion and considering the public…`
  - nj:     `Inherent uncertainties in the measurement of greenhouse gas emissions The Council has chosen to include a measure of its greenhouse gas (GHG) emissions in its performance information. Without modifying our opinion and considering the public…`

### Wellington City Council

- **Description 1**
  - target: `Statement of service provision: Measurement and reporting of Wellington City Council Group greenhouse gas emissions. The Council has chosen to include a measure of the quantity of greenhouse gas (GHG) emissions from the Council and Group in…`
  - nj:     `Statement of service provision: Measurement and reporting of Wellington City Council Group greenhouse gas emissions. The Council has chosen to include a measure of the quantity of greenhouse gas (GHG) emissions from the Council and Group in…`
- **Description 4**
  - target: `Future of water delivery. Note 40 on pages 121 to 122 of Volume 2 outlines that in response to the Government’s Local Water Done Well reforms, the Council has decided to establish a multi-owned water organisation with Hutt City, Porirua Cit…`
  - nj:     `Future of water delivery. Note 40 on pages 153 to 154 of Volume 2 outlines that in response to the Government’s Local Water Done Well reforms, the Council has decided to establish a multi-owned water organisation with Hutt City, Porirua Cit…`
- **Nature 5**
  - target: `Uncertainty over the fair value of three waters assets`
  - nj:     `Three waters assets`
- **Description 5**
  - target: `Uncertainty over the fair value of three waters asset. Without modifying our opinion, we draw attention Page 62 to 63 of the financial statements in Volume 2 outlines the significant uncertainties over the fair value of three waters assets …`
  - nj:     `Uncertainty over the fair value of three waters asset. Without modifying our opinion, we draw attention Page 72 to 73 of the financial statements in Volume 2 outlines the significant uncertainties over the fair value of three waters assets …`

### West Coast Regional Council

- **Nature 2**
  - target: `Financial statements`
  - nj:     `Financial statement`

### Whakatane District Council

- **Nature 5**
  - target: `Inherent uncertainties in the measurement of greenhouse gas emissions`
  - nj:     `Greenhouse gas emissions`
