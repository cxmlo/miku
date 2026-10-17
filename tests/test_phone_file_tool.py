import json
import io
import os
import urllib.request

import tools_miku


def test_send_file_tool_uses_authenticated_phone_endpoint(monkeypatch, tmp_path):
    source = tmp_path / "phone-image.png"
    source.write_bytes(b"image-content")
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return json.dumps({"status": "ok", "filename": source.name}).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setenv("MIKU_API_KEY", "test-api-key")
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    result = tools_miku.enviar_archivo_a_celular(str(source))

    request = captured["request"]
    assert request.full_url == "http://127.0.0.1:8000/api/desktop/send_file_to_phone"
    assert json.loads(request.data) == {"path": os.path.abspath(source)}
    assert any(
        name.lower() == "x-api-key" and value == "test-api-key"
        for name, value in request.header_items()
    )
    assert captured["timeout"] == 5
    assert "phone-image.png" in result


def test_send_file_tool_reports_missing_phone_error(monkeypatch, tmp_path):
    import urllib.error

    source = tmp_path / "phone-image.png"
    source.write_bytes(b"image-content")

    def disconnected(*_args, **_kwargs):
        raise urllib.error.HTTPError(
            "http://127.0.0.1:8000/api/desktop/send_file_to_phone",
            409,
            "Conflict",
            {},
            io.BytesIO(b'{"detail":"No hay un telefono Miku conectado."}'),
        )

    monkeypatch.setattr(urllib.request, "urlopen", disconnected)

    result = tools_miku.enviar_archivo_a_celular(str(source))

    assert "HTTP 409" in result
