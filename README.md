# Council Audits Map

An interactive map of NZ council audit findings, built with [Observable Framework](https://observablehq.com/framework/).

## Getting started

Install dependencies:

```
yarn install
```

Start the local preview server:

```
yarn dev
```

Then visit <http://localhost:3000> to preview the app.

## Data preprocessing

The raw data source is `Final LG Audit Opinion Dashboard Content.csv`. To regenerate the clean dataset:

```
python scripts/geocode_councils.py      # produces src/data/council-coordinates.json
python scripts/preprocess_councils.py   # produces src/data/CouncilsAuditData2025.csv
```

## Project structure

```ini
.
├─ scripts
│  ├─ geocode_councils.py        # one-time geocoding script
│  ├─ preprocess_councils.py     # CSV preprocessing script
│  └─ test_puppeteer.cjs         # Puppeteer test helper
├─ src
│  ├─ components
│  │  └─ utils.js                # map, filter, and table logic
│  ├─ data
│  │  ├─ CouncilsAuditData2025.csv    # preprocessed council data
│  │  └─ council-coordinates.json     # geocoded council locations
│  ├─ custom.css                 # app styles
│  └─ index.md                   # the home page
├─ observablehq.config.js        # the app config file
├─ package.json
└─ README.md
```

## Command reference

| Command           | Description                                              |
| ----------------- | -------------------------------------------------------- |
| `yarn install`    | Install or reinstall dependencies                        |
| `yarn dev`        | Start local preview server                               |
| `yarn build`      | Build your static site, generating `./dist`              |
| `yarn deploy`     | Deploy your app to Observable                            |
| `yarn clean`      | Clear the local data loader cache                        |
| `yarn observable` | Run commands like `observable help`                      |
