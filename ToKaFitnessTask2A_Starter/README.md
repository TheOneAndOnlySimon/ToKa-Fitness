# ToKa Fitness / ToKa Online — Task 2A Starter

A deliberately basic Flask + SQLite + JavaScript prototype starter for the ToKa Fitness Task 2A development activity.

## Run in PyCharm (Windows)

1. Extract the ZIP file.
2. Open the extracted `ToKaFitnessTask2A_Starter` folder in PyCharm.
3. Open the PyCharm terminal.
4. Create a virtual environment (recommended):

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

5. Install the dependency:

   ```bash
   pip install -r requirements.txt
   ```

6. Run `run.py`, or use the terminal:

   ```bash
   python run.py
   ```

7. Open the local address shown in the terminal (normally `http://127.0.0.1:5000`).

The SQLite database `toka_fitness.db` is created automatically the first time the app runs. It is not included in the ZIP because it is generated locally.

## Included starter functionality

- Public home page and free resources library.
- Keyword and category search using parameterised SQLite queries.
- Account registration and login using Werkzeug password hashing.
- Five failed login attempts trigger a 15-minute lockout.
- Free accounts by default; paid guide routes check membership on the server.
- A demo-only membership upgrade button (does not take payment).
- Logged-in users can create and delete their own workout/eating plans.
- Basic community posting and report/hide behaviour.
- Demonstration points ledger with a unique constraint to prevent duplicate awards.
- JavaScript text-size and high-contrast controls.

## Important limitations / work still required

This is a learning prototype, not a production-ready fitness service.

- Replace all sample health and fitness content with content reviewed and approved by qualified ToKa staff. Add reliable sources to every guide.
- The demo upgrade is not payment processing. Integrate a suitable provider and implement renewals, expiry, cancellation and payment confirmation.
- The demo completion route accepts a reference in the URL. It does not prove that a workout was completed. Build server-verified session tracking before awarding real points.
- Community moderation is minimal. Add staff roles, a moderation dashboard, rate limiting, safe content handling and an audit trail.
- The contact form currently displays a confirmation but does not save enquiries.
- Password reset, admin MFA, full role-based administration, friends, replies, avatar shop, meal logging, progress charts and staff content management are not implemented.
- Add CSRF protection, secure production session settings, HTTPS, privacy/cookie notices, retention controls and appropriate consent before any real deployment.
- Test keyboard use, screen-reader output, contrast ratios and 200% zoom. The controls here are a starting point, not proof of WCAG 2.2 AA compliance.
- Set `debug=False` and use a production WSGI server before deployment.

## Useful places to start editing

- `app.py` — Flask routes, validation and SQLite operations.
- `templates/` — page structure and Jinja templates.
- `static/css/style.css` — colours, layout and responsive styling.
- `static/js/main.js` — browser-side interactions.
- `schema.sql` — reference copy of the database structure.

## AI-generated code and your Task 1 Activity C log

The starter adapts the five Task 1 AI-code areas:
1. Password hashing/checking — registration and login use Werkzeug.
2. Paid-content access — `require_member` checks the current database membership status.
3. Saving plans — the `/plans` route uses the logged-in session user ID.
4. Searching content — `/resources` uses parameterised `LIKE` queries.
5. Duplicate reward prevention — `points_ledger` has a unique `(user_id, completion_id)` constraint.

These snippets have been adapted to this project's schema and connected to surrounding routes. Record the changes you make, run your own tests, and update your AI log accurately. Do not claim a feature has been tested until you have tested it yourself.
