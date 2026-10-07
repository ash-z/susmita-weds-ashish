"""3D branch only: copy the dev previews to build/artifact-3d[-friends|-groom].html, relabelled 3D, so this branch's
previews are separate artifacts and never overwrite the dev ones. Run after build.py."""
import pathlib
b = pathlib.Path(__file__).resolve().parent / "build"
for suf in ("", "-friends", "-groom"):
    t = (b / f"artifact-dev{suf}.html").read_text()
    t = t.replace("(dev", "(3D dev", 1).replace('letter-spacing:.12em">DEV</div>', 'letter-spacing:.12em">3D DEV</div>', 1)
    assert "3D DEV" in t and "(3D dev" in t, suf
    (b / f"artifact-3d{suf}.html").write_text(t)
print("wrote build/artifact-3d{,-friends,-groom}.html")
