# Mapping Project

This project generates a simple map website using `uv` (Python) and Leaflet (JavaScript).

## Running Tests

### JavaScript Tests

The logic for the map (filtering, opening hours, etc.) is written in JavaScript and tested using Jest.

To run the JavaScript tests:

1.  **Install dependencies** (first time only):
    ```bash
    npm install
    ```

2.  **Run tests**:
    ```bash
    npm test
    ```

### Python Tests

To run the Python tests (for the build process):

```bash
uv run python -m pytest
```

## Building the Website

To build `index.html`:

```bash
uv run build.py
```

## Project Structure

- `build.py`: Python script to generate `index.html`.
- `generate_qr.py` : Python script to generate QR codes.
- `js/`: JavaScript source files.
  - `logic.js`: Pure logic (tested).
  - `main.js`: UI and Map initialization.
- `tests/`: Test files.
  - `logic.test.js`: JavaScript tests.
  - `test_*.py`: Python tests.
