from daily_signal.cli import main


def test_seed_sources_bad_config_returns_2(tmp_path, capsys) -> None:
    bad = tmp_path / "sources.yaml"
    bad.write_text(
        "version: 1\nsources: []\npermission_defaults: {review_status: approved}\n",
        encoding="utf-8",
    )
    assert main(["seed-sources", "--config", str(bad)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "seed-sources:" in captured.err
