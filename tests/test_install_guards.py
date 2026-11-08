"""
godot install 守卫测试: stable-only 门禁与 Ctrl+C 取消.

非 stable 输入 (rc/beta/alpha/dev) 在触碰网络与磁盘前即被拒绝;
Ctrl+C 下载阶段清理半成品并以 130 干净退出.
"""

from __future__ import annotations

from click.testing import CliRunner

from gdpm.cli.commands.godot.common import normalize_version
from gdpm.cli.commands.godot.install import _is_stable_tag, godot_install
from gdpm.utils.install import get_godot_ext, get_godot_platform


def test_stable_tag_predicate() -> None:
    """门禁谓词: stable 通过, 非 stable (含 normalize 产物) 拒绝."""
    assert _is_stable_tag(normalize_version("4.7"))
    assert _is_stable_tag(normalize_version("4.7-stable"))
    assert _is_stable_tag(normalize_version("4.7-csharp"))
    assert not _is_stable_tag(normalize_version("4.8-beta2"))
    assert not _is_stable_tag(normalize_version("4.7-rc1"))
    assert not _is_stable_tag(normalize_version("4.8-alpha1"))
    # normalize 对 dev 会追加 -stable, 拼接结果仍应被识别为非 stable
    assert not _is_stable_tag(normalize_version("4.9-dev"))


def test_install_rejects_non_stable_before_network() -> None:
    """非 stable 版本直接报错, 不进入下载流程."""
    for version in ("4.8-beta2", "4.7-rc1", "4.9-dev"):
        result = CliRunner().invoke(godot_install, [version])
        assert result.exit_code == 0, version
        assert "not supported" in result.output, version
        assert "stable releases only" in result.output, version


def test_install_cancel_cleans_partial(tmp_path, monkeypatch) -> None:
    """Ctrl+C 下载阶段: 半成品压缩包被清理, 以 130 干净退出."""
    monkeypatch.setattr(
        "gdpm.cli.commands.godot.install.get_engines_dir", lambda: tmp_path
    )

    def _interrupt(*args: object, **kwargs: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(
        "gdpm.cli.commands.godot.install.download_file_chunked", _interrupt
    )
    # 预置半成品, 证明取消路径真的执行了清理
    stale = tmp_path / (f"Godot_v4.7-stable_{get_godot_platform()}.{get_godot_ext()}")
    stale.write_bytes(b"partial")

    result = CliRunner().invoke(godot_install, ["4.7"])

    assert result.exit_code == 130
    assert "Cancelled" in result.output
    assert not stale.exists()
    assert not (tmp_path / "4.7-stable").exists()
