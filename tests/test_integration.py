"""Integration test: drive the Flask route against a real MySQL database.

Requires a reachable MySQL 8 instance configured through the DB_USER / DB_PASS /
DB_HOST / DB_NAME environment variables (the CI pipeline provides one as a service
container). Run with:  pytest tests/test_integration.py
"""
import app as application


def test_convert_and_store():
    # disable CSRF so the test client can POST the form directly
    application.app.config["WTF_CSRF_ENABLED"] = False
    client = application.app.test_client()

    # make sure the schema exists (tolerant of ordering)
    with application.app.app_context():
        application.db.create_all()

    resp = client.post("/", data={"celsius": "37"})
    assert resp.status_code == 200

    # the conversion (37 C -> 98.6 F) must be persisted in MySQL
    with application.app.app_context():
        rows = application.Temperature.query.all()
        assert any(round(r.fahrenheit, 2) == 98.6 for r in rows)
