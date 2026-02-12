# AGENTS instructions

## The Project

This project is to create a simple fast-loading website to direct people to local businesses. In a limited geographical area.
People will most often access the website via a qr code that is tied to a certain location.
The businesses should be filterable by different things like distance, category, is open now, or will open soon.
The website should be fast to load and have a good user experience. This project uses uv commands.
Please keep Javascript to be as fast as possible to load and to run. So should likely be vanilla, and not grow in a large size.

## Tooling

### python

everything is managed via uv, so add dependencies properly using uv and python commands are to use uv

### javascript

npm and node are managed by volta
everything is managed via npm, so add dependencies properly using npm
biome is used for to format the code

## Building the website

```shell
uv run build.py
```

This command requires `data.toml` to exist. It's where all the information used to actually generate the website should exist. 

## Building the QR codes

```shell
uv run generate_qr.py
```

this command requires `data.toml` to exist. It uses information in it to generate qr codes for each location.

## Data format 

See `data.toml` for the format of the data for a business and for a location.

## Running python tests

```shell
uv run python -m pytest
```

## Running javascript tests
```shell
npm test
```
This runs both unit tests (`tests/logic.test.js`) and UI/DOM tests (`tests/ui.test.js`).
UI tests use `jest-environment-jsdom` to test DOM rendering functions from `main.js` (card rendering, list view, dropdown building and interaction).

## running static checkers

```shell
npx @biomejs/biome lint --write
```

## files
do not edit `index.html` and `index_unminified.html` are generated files
`data.toml` is the source of truth for the data. It should also be very easy to edit for others to add values to it.