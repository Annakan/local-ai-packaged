import tempfile
import pytest
import tomlkit
from subprocess import run
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "generate_secrets.py"

template_content = '''
SECRET_KEY = "<RAND>"
ADMIN_PASSWORD = "<PASSWD>"
USER_TOKEN = "<JWT:user:local=SECRET_KEY>"

[database]
password = "<PASSWD>"

[[services]]
name = "service1"
secret = "<RAND>"

[[services]]
name = "service2"
secret = "<RAND>"

[nested]
  [nested.inner]
  JWT_SECRET = "<RAND>" 
  jwt = "<JWT:admin:issuer=JWT_SECRET>"
'''

def test_generate_secrets(tmp_path):
    template_file = tmp_path / ".secrets.toml.tpl"
    output_file = tmp_path / ".secrets.toml"
    template_file.write_text(template_content)

    result = run([
        "python3", str(SCRIPT),
        "--template", str(template_file),
        "--output", str(output_file),
        "--master-password", "testmaster"
    ], capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    content = output_file.read_text()
    doc = tomlkit.parse(content)
    assert "SECRET_KEY" in doc
    assert len(doc["SECRET_KEY"]) >= 16
    assert "ADMIN_PASSWORD" in doc
    assert doc["ADMIN_PASSWORD"] == "testmaster"
    assert "USER_TOKEN" in doc
    assert doc["USER_TOKEN"].count('.') == 2  # JWT has 2 dots

def test_generate_secrets_nested(tmp_path):
    template_file = tmp_path / ".secrets.toml.tpl"
    output_file = tmp_path / ".secrets.toml"
    template_file.write_text(template_content)

    result = run([
        "python3", str(SCRIPT),
        "--template", str(template_file),
        "--output", str(output_file),
        "--master-password", "testmaster"
    ], capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    content = output_file.read_text()
    doc = tomlkit.parse(content)

    # Top-level
    assert "SECRET_KEY" in doc
    assert len(doc["SECRET_KEY"]) >= 16
    assert "ADMIN_PASSWORD" in doc
    assert doc["ADMIN_PASSWORD"] == "testmaster"
    assert "USER_TOKEN" in doc
    assert doc["USER_TOKEN"].count('.') == 2  # JWT has 2 dots

    # Table
    assert "database" in doc
    assert doc["database"]["password"] == "testmaster"

    # Array of tables
    assert "services" in doc
    assert isinstance(doc["services"], list)
    assert len(doc["services"]) == 2
    for service in doc["services"]:
        assert "secret" in service
        assert len(service["secret"]) >= 16

    # Nested table
    assert "nested" in doc
    assert "inner" in doc["nested"]
    assert doc["nested"]["inner"]["jwt"].count('.') == 2
