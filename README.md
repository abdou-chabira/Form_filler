# Paycheck Field Printer (Django)

This app lets you:

1. Upload a scanned paycheck image.
2. Store the real paper dimensions in millimeters.
3. Draw text input zones directly on the image.
4. Fill values and print so text lands on the exact paper fields.

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run migrations:

```bash
python manage.py migrate
```

4. Start server:

```bash
python manage.py runserver
```

5. Open `http://127.0.0.1:8000/`.

## Run With Docker

1. Copy `.env.example` to `.env` and adjust values if needed.
2. Build and start the app:

```bash
docker compose up --build
```

3. Open `http://127.0.0.1:8000/`.

Notes:

- Startup automatically runs `migrate` and `collectstatic`.
- `media` and SQLite data are persisted in Docker named volumes.
- Stop containers with:

```bash
docker compose down
```

## Usage Flow

1. Click **New Template**.
2. Upload scanned check image and enter actual width/height in mm.
3. In **Design**, drag to create each text field (date, payee, amount, etc.).
4. Fill field values.
5. Click print and print at **100% / Actual size** in the printer dialog.

## Accuracy Tips

- Always disable printer scaling (Fit to page must be off).
- Use high-resolution scans (300 DPI or above).
- Test with plain paper first and adjust field boxes.
- If your printer has margins that cannot be removed, account for this by offsetting field positions in the designer.
