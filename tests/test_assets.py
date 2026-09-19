import hashlib
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APPROVED_SVG_SHA256 = "a76b822723cb30b0ac4985238cbc1e48ce37ddbc5ca33993f5fc2d783332f205"


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"not a PNG file: {path}")
    return struct.unpack(">II", data[16:24])


class AssetContractTest(unittest.TestCase):
    def test_svg_is_exact_approved_copy(self):
        self.assertEqual(
            APPROVED_SVG_SHA256,
            hashlib.sha256((ROOT / "assets/logo.svg").read_bytes()).hexdigest(),
        )

    def test_official_png_and_composer_icon_have_expected_dimensions(self):
        self.assertEqual((873, 873), png_size(ROOT / "assets/official-logo.png"))
        self.assertEqual((256, 256), png_size(ROOT / "assets/composer-icon.png"))

    def test_setup_uses_the_full_official_wordmark(self):
        html = (ROOT / "assets/setup/index.html").read_text()
        self.assertIn('src="/official-logo.png"', html)
        self.assertIn('width="180"', html)
        self.assertIn('height="52"', html)


if __name__ == "__main__":
    unittest.main()
