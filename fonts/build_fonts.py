"""Convert the installed Latin Modern OpenType faces to web font files.

Requires fonttools[woff] and a TeX installation that provides Latin Modern.
The generated WOFF2 files are committed so the website has no build dependency.
"""

from pathlib import Path
import subprocess

from fontTools.ttLib import TTFont


FACES = (
    "lmroman10-regular",
    "lmroman10-bold",
    "lmroman10-italic",
    "lmroman10-bolditalic",
    "lmsans10-regular",
    "lmsans10-bold",
)


def main() -> None:
    for face in FACES:
        source = subprocess.check_output(
            ["kpsewhich", f"{face}.otf"], text=True
        ).strip()
        if not source:
            raise FileNotFoundError(f"{face}.otf is missing from the TeX installation")
        font = TTFont(source)
        font.flavor = "woff2"
        font.save(Path(__file__).parent / f"{face}.woff2")


if __name__ == "__main__":
    main()
