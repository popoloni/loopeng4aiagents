"""Offline runtime integrity, path, download and owned-child lifecycle tests."""
import hashlib
import io
import json
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from loopeng.runtime import local_model as lm


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.archive = self.root / "release.tar.gz"
        with tarfile.open(self.archive, "w:gz") as archive:
            directory = tarfile.TarInfo("llama-b11799")
            directory.type = tarfile.DIRTYPE
            archive.addfile(directory)
            for name in ("llama-server", "libexample.so.1"):
                data = b"test binary"
                member = tarfile.TarInfo("llama-b11799/" + name)
                member.mode, member.size = 0o755, len(data)
                archive.addfile(member, io.BytesIO(data))
            link = tarfile.TarInfo("llama-b11799/libexample.so")
            link.type, link.linkname = tarfile.SYMTYPE, "libexample.so.1"
            archive.addfile(link)
        self.model = self.root / "model.gguf"
        self.model.write_bytes(b"model")
        self.runtime = self.root / "runtime"
        for name, value in (("ARTIFACTS", {"DarwinARM64": ("release.tar.gz", lm.sha256(self.archive), self.archive.stat().st_size)}),
                            ("MODEL_SHA256", lm.sha256(self.model)), ("MODEL_BYTES", 5)):
            context = patch.object(lm, name, value)
            context.start()
            self.addCleanup(context.stop)

    def prepare(self):
        lm.setup(self.runtime, "DarwinARM64", self.archive, self.model, False)

    def test_setup_offline_and_integrity(self):
        with patch.object(lm.urllib.request, "urlopen", side_effect=AssertionError("network")):
            self.prepare()
        self.assertTrue(lm.verify_runtime(self.runtime, self.model, "DarwinARM64").is_file())
        self.assertTrue((self.runtime / "llama-b11799/libexample.so").is_symlink())
        with self.assertRaises(FileExistsError):
            self.prepare()

    def test_library_tamper_rejected(self):
        self.prepare()
        (self.runtime / "llama-b11799/libexample.so.1").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "mismatch"):
            lm.verify_runtime(self.runtime, self.model, "DarwinARM64")

    def test_model_tamper_rejected(self):
        self.prepare()
        self.model.write_bytes(b"other")
        with self.assertRaisesRegex(ValueError, "mismatch"):
            lm.verify_runtime(self.runtime, self.model, "DarwinARM64")

    def test_extra_library_rejected(self):
        self.prepare()
        (self.runtime / "llama-b11799/injected.so").write_bytes(b"extra")
        with self.assertRaisesRegex(ValueError, "Unexpected"):
            lm.verify_runtime(self.runtime, self.model, "DarwinARM64")

    def test_download_requires_opt_in_before_writes(self):
        with self.assertRaisesRegex(ValueError, "allow-download"):
            lm.setup(self.runtime, "DarwinARM64", None, self.model, False)
        self.assertFalse(self.runtime.exists())

    def test_external_outputs_and_symlinks(self):
        for path in (lm.REPO / "runtime-new", lm.REPO, lm.REPO.parent):
            with self.assertRaises(ValueError):
                lm.external_path(path)
        link = self.root / "link"
        link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            lm.fresh_directory(link / "new")

    def test_archive_traversal_and_links(self):
        for name, link in (("../evil", None), ("llama-b11799/link", "../../evil")):
            member = tarfile.TarInfo(name)
            if link:
                member.type, member.linkname = tarfile.SYMTYPE, link
            bundle = MagicMock()
            bundle.getmembers.return_value = [member]
            with self.assertRaises(ValueError):
                lm.archive_members(bundle)

    def test_download_integrity_and_partial_retention(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.side_effect = [b"abc", b""]
        destination = self.root / "download"
        with patch.object(lm.urllib.request, "urlopen", return_value=response):
            lm.download("https://example.invalid", destination, hashlib.sha256(b"abc").hexdigest(), 3)
        self.assertEqual(destination.read_bytes(), b"abc")
        response.read.side_effect = [b"bad", b""]
        with patch.object(lm.urllib.request, "urlopen", return_value=response):
            with self.assertRaises(ValueError):
                lm.download("https://example.invalid", self.root / "bad", "0" * 64, 3)
        self.assertTrue((self.root / "bad.partial").exists())
        self.assertFalse((self.root / "bad").exists())

    def test_metal_is_explicit(self):
        command = lm.server_command(Path("server"), Path("model"), 18080, False)
        self.assertEqual(command[command.index("--n-gpu-layers") + 1], "0")
        self.assertIn("--no-agent", command)
        self.assertIn("99", lm.server_command(Path("server"), Path("model"), 18080, True))

    def test_owned_process_killed_after_grace(self):
        self.prepare()
        process = MagicMock()
        process.poll.return_value = None
        process.pid, process.returncode = 1234, -9
        process.wait.side_effect = [subprocess.TimeoutExpired("server", 1), -9]
        evidence = self.root / "evidence"
        with patch.object(lm, "host_target", return_value="DarwinARM64"), \
             patch.object(lm.subprocess, "Popen", return_value=process), \
             patch.object(lm.socket, "socket"), \
             patch.object(lm.time, "monotonic", side_effect=[0, 10, 11]):
            self.assertEqual(lm.serve(self.runtime, self.model, evidence, 18080, True, 1, 1, 1), 1)
        process.terminate.assert_called_once()
        process.kill.assert_called_once()
        self.assertTrue(json.loads((evidence / "FINISH.json").read_text())["forced_kill"])

    def test_linux_rejects_metal_before_launch(self):
        with patch.object(lm, "host_target", return_value="Linuxx64"):
            with self.assertRaisesRegex(ValueError, "Darwin"):
                lm.serve(self.runtime, self.model, self.root / "out", 18080, True, 1, 1, 1)


if __name__ == "__main__":
    unittest.main()
