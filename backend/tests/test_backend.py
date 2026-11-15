"""Offline tests: no network. Remote files are replaced by FITS files built in memory."""

import io

import numpy as np
import pytest
from astropy.io import fits
from astropy.wcs import WCS

from app import align, archive, pipeline, prepare, render

RA, DEC = 150.0, 20.0


def make_wcs(angle_deg=0.0, n=200):
    w = WCS(naxis=2)
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.crval = [RA, DEC]
    w.wcs.crpix = [n / 2 + 0.5, n / 2 + 0.5]
    s, a = 6.14 / 3600, np.radians(angle_deg)
    w.wcs.cd = [[-s * np.cos(a), s * np.sin(a)], [s * np.sin(a), s * np.cos(a)]]
    return w


def make_file(compressed_flags: bool, n=200):
    rng = np.random.default_rng(1)
    image = rng.normal(5, 1, (n, n)).astype("f4")
    flags = rng.integers(0, 2**28, (n, n)).astype("i4")
    hdr = make_wcs(n=n).to_header()
    hdr["MJD-AVG"], hdr["DATE-AVG"] = 60900.5, "2025-08-13T12:00:00"
    flag_hdu = (fits.CompImageHDU(flags, name="FLAGS", compression_type="RICE_1", tile_shape=(1, n))
                if compressed_flags else fits.ImageHDU(flags, name="FLAGS"))
    hdus = fits.HDUList([fits.PrimaryHDU(), fits.ImageHDU(image, hdr, name="IMAGE"), flag_hdu,
                         fits.ImageHDU(image * 2, name="VARIANCE")])
    buf = io.BytesIO()
    hdus.writeto(buf)
    return buf.getvalue(), image, flags


@pytest.fixture
def remote(monkeypatch):
    files = {}

    def read_range(url, start, length, tries=1):
        data = files[url]
        return data[start : start + length] if start >= 0 else data[-length:]

    monkeypatch.setattr(archive, "read_range", read_range)
    return files


@pytest.mark.parametrize("compressed", [False, True])
def test_cutout_matches_full_file(remote, compressed):
    remote["f"], image, flags = make_file(compressed)
    cut = archive.cutout("f", RA, DEC, 10, wanted=("IMAGE", "FLAGS", "VARIANCE"))
    x0, x1, y0, y1 = cut["box"]
    assert (x1 - x0, y1 - y0) == (21, 21)
    assert np.array_equal(cut["IMAGE"], image[y0:y1, x0:x1])
    assert np.array_equal(cut["FLAGS"], flags[y0:y1, x0:x1])
    assert np.array_equal(cut["VARIANCE"], image[y0:y1, x0:x1] * 2)


def test_cutout_is_clipped_at_the_detector_edge(remote):
    remote["f"], image, _ = make_file(False)
    ra, dec = make_wcs().pixel_to_world_values(2, 100)
    cut = archive.cutout("f", float(ra), float(dec), 10)
    assert cut["box"] == (0, 13, 90, 111)
    assert cut["IMAGE"].shape == (21, 13)


def test_cutout_cache_downloads_once(remote, tmp_path, monkeypatch):
    monkeypatch.setattr(archive.config, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(archive, "wave_table", lambda url, det: None)
    remote["f"], _, _ = make_file(True)
    exposure = {"id": "x", "url": "f", "detector": 2, "mjd": 60900.0}
    first = archive.fetch_cutout(exposure, RA, DEC, 10)
    remote.clear()  # a second download would now fail
    second = archive.fetch_cutout(exposure, RA, DEC, 10)
    assert (first["cached"], second["cached"]) == (False, True)
    assert np.array_equal(first["image"], second["image"])
    assert second["mjd"] == 60900.5


def test_wavelength_interpolation():
    xs, ys = np.array([1.0, 1001.0, 2001.0]), np.array([1.0, 2001.0])
    values = np.zeros((2, 3, 2))
    values[..., 0] = [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0]]  # wavelength rises with y
    values[..., 1] = 0.03
    wave, width = archive.wavelength_at((xs, ys, values), 500, 1000)
    assert wave == pytest.approx(1.5, abs=1e-6) and width == pytest.approx(0.03)
    assert archive.wavelength_at(None, 0, 0) == (None, None)


def test_exposure_id_ignores_processing_version():
    url = "https://x/dr1/level2/2025W33_2C/l2b-v27-2026-228/3/level2_2025W33_2C_0321_1D3_spx_l2b-v27-2026-228.fits"
    assert archive.exposure_id(url) == "level2_2025W33_2C_0321_1D3"


def test_prepare_removes_background_and_repairs_pixels():
    rng = np.random.default_rng(2)
    image = rng.normal(10, 0.1, (41, 41)).astype("f4")
    flags = np.full(image.shape, 1 << prepare.FLAG_BITS["SOURCE"], "i4")  # "known source" everywhere
    image[18:23, 18:23] += 50  # a bright star...
    image[20, 20] = np.nan     # ...with a blown-out centre
    flags[20, 20] |= 1 << prepare.FLAG_BITS["OVERFLOW"]
    image[5, 5] = 500          # a cosmic-ray hit
    flags[5, 5] |= 1 << prepare.FLAG_BITS["TRANSIENT"]
    clean, stats = prepare.prepare(image, flags)
    assert np.isfinite(clean).all()
    assert abs(np.median(clean)) < 0.05 and stats["background"] == pytest.approx(10, abs=0.05)
    assert clean[20, 20] > 45        # the core is bright, not a black hole
    assert abs(clean[5, 5]) < 1      # the hit is gone
    assert stats["bad_fraction"] < 0.01  # the SOURCE flag is not counted as bad


def test_flag_names():
    assert prepare.flag_names((1 << 21) | 1) == ["TRANSIENT", "SOURCE"]


@pytest.mark.parametrize("angle", [0, 37, 180, 250])
def test_star_lands_on_the_same_pixel_at_any_rotation(angle):
    wcs = make_wcs(angle)
    ra, dec = RA + 0.01, DEC - 0.008
    x, y = wcs.world_to_pixel_values(ra, dec)
    yy, xx = np.mgrid[:200, :200]
    image = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / 2).astype("f4")
    grid, size, scale = align.target_grid(RA, DEC, 10.0)
    out = align.align(image, wcs, grid, size)
    assert out.shape == (size, size) and scale == pytest.approx(6.14 / 3)
    ey, ex = grid.world_to_pixel_values(ra, dec)[::-1]
    gy, gx = np.mgrid[:size, :size]
    weight = np.nan_to_num(out)
    cx, cy = (weight * gx).sum() / weight.sum(), (weight * gy).sum() / weight.sum()
    assert np.hypot(cx - ex, cy - ey) * scale < 0.5 * 6.14 / 3  # well under half a native pixel


def test_grid_is_north_up_east_left():
    grid, size, _ = align.target_grid(RA, DEC, 10.0)
    x_n, y_n = grid.world_to_pixel_values(RA, DEC + 0.01)
    x_e, y_e = grid.world_to_pixel_values(RA + 0.01, DEC)
    centre = (size - 1) / 2
    assert y_n > centre and x_n == pytest.approx(centre, abs=0.01)
    assert x_e < centre
    assert align.cutout_half_size(10.0) * 2 * 6.14 > 600 * np.sqrt(2)


def test_png_is_flipped_and_handles_blank_pixels():
    from PIL import Image

    frame = np.zeros((4, 4), "f4")
    frame[3, 0] = 100   # top-left on the sky (last FITS row)
    frame[0, 3] = np.nan
    low, high, soft = render.stretch_limits([frame], 1.0)
    pixels = np.array(Image.open(io.BytesIO(render.to_png(frame, low, high, soft))))
    assert pixels.shape == (4, 4) and pixels[0, 0] == 255 and pixels[3, 3] == 0


def test_seasons_and_even_pick():
    assert pipeline.assign_seasons([1, 2, 31, 70, 71, 200]) == [0, 0, 0, 1, 1, 2]
    picked = pipeline.pick_evenly(list(range(100)), 10)
    assert len(picked) == 10 and picked[0] == 0 and picked[-1] == 99
    assert pipeline.pick_evenly([1, 2], 10) == [1, 2]


def test_api_rejects_bad_input_and_serves_cached_result(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from app import config, main

    monkeypatch.setattr(config, "CACHE_DIR", tmp_path)
    client = TestClient(main.app)
    assert client.get("/api/health").json()["status"] == "ok"
    assert client.get("/api/frames", params={"ra": 400, "dec": 0}).status_code == 422
    assert client.get("/api/frames", params={"ra": 10, "dec": 0, "fov": 500}).status_code == 422
    assert client.get("/api/frames", params={"ra": 10, "dec": 0, "band": 7}).status_code == 422
    assert client.get("/api/frames", params={"ra": 10, "dec": 0, "mode": "nonsense"}).status_code == 422
    assert client.get("/api/frame/../../etc/passwd.png").status_code == 404
    assert client.get("/api/frame/0123456789abcdef/000.png").status_code == 404

    key = pipeline.request_key(10.0, 0.0, 10.0, 2, "exposures")
    path = pipeline.result_path(key)
    path.parent.mkdir(parents=True)
    path.write_text('{"status": "done", "frames": []}')
    (path.parent / "000.png").write_bytes(b"png")
    assert client.get("/api/frames", params={"ra": 10, "dec": 0}).json() == {"status": "done", "frames": []}
    assert client.get(f"/api/frame/{key}/000.png").content == b"png"


def test_starter_cache_is_used_when_the_live_cache_is_empty(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from app import config, main

    monkeypatch.setattr(config, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(config, "SEED_DIR", tmp_path / "seed")
    key = pipeline.request_key(20.0, 5.0, 10.0, 2, "exposures")
    folder = tmp_path / "seed" / "frames" / key
    folder.mkdir(parents=True)
    (folder / "result.json").write_text('{"status": "done", "frames": []}')
    (folder / "000.png").write_bytes(b"png")
    search = tmp_path / "seed" / "search"
    search.mkdir()
    (search / "spherex_dr1_20.0000_5.0000.json").write_text("[]")

    client = TestClient(main.app)
    assert client.get("/api/frames", params={"ra": 20, "dec": 5}).json()["status"] == "done"
    assert client.get(f"/api/frame/{key}/000.png").content == b"png"
    assert archive._search_one("spherex_dr1", 20.0, 5.0) == []  # no network call


def test_season_stack_removes_one_off_artefacts_and_lowers_noise():
    rng = np.random.default_rng(3)
    group = []
    for i in range(15):
        image = rng.normal(0, 1, (40, 40)).astype("f4")
        image[20, 20] += 3          # a faint star, hidden in the noise of one exposure
        if i == 4:
            image[5, 5] = 1000      # an artefact in a single exposure
        group.append({"image": image, "mjd": 60900.0 + i, "date": f"2025-08-{13 + i:02d}T00:00:00",
                      "wavelength_um": 1.1 + 0.03 * i, "bad_fraction": 0.01, "saturated_pixels": 0,
                      "target_flags": ["SOURCE"] if i % 2 else [],
                      "flag_fractions": {"SOURCE": 0.4, "HOT": 0.02} if i % 2 else {"SOURCE": 0.2},
                      "exposure": {"detector": 2, "collection": "spherex_dr1", "irsa_url": "u", "id": str(i)}})
    stack = pipeline.stack_season(1, group)
    image = stack["image"]
    assert abs(image[5, 5]) < 2                       # the artefact is gone
    assert pipeline.image_noise(image) < 0.45         # about 1 / sqrt(15) * 1.25
    assert image[20, 20] > 5 * pipeline.image_noise(image)  # the star now stands out
    assert stack["n_exposures"] == 15 and stack["season"] == 1
    assert (stack["wavelength_min_um"], stack["wavelength_max_um"]) == (1.1, 1.52)
    assert stack["time_start"].startswith("2025-08-13") and stack["time_end"].startswith("2025-08-27")
    assert stack["target_flags"] == ["SOURCE"]
    assert stack["flag_fractions"]["SOURCE"] == pytest.approx(0.2933, abs=1e-3)   # mean over the visit
    assert stack["flag_fractions"]["HOT"] == pytest.approx(0.02 * 7 / 15, abs=1e-3)


def test_gaia_stars_are_parsed_and_cached(tmp_path, monkeypatch):
    from app import config, overlays

    monkeypatch.setattr(config, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(config, "SEED_DIR", tmp_path / "seed")
    calls = []

    class Answer:
        text = ("source_id,ra,dec,pmra,pmdec,parallax,phot_g_mean_mag\n"
                "4472832130942575872,269.4485,4.7394,-801.55,10362.39,546.98,8.19\n"
                "123,269.5,4.7,,,,15.2\n")

        def raise_for_status(self):
            pass

    def post(url, data, timeout):
        calls.append(data["QUERY"])
        return Answer()

    monkeypatch.setattr(overlays.requests, "post", post)
    first = overlays.gaia_stars(269.44627, 4.76819, 10.0)
    second = overlays.gaia_stars(269.44627, 4.76819, 10.0)
    assert len(calls) == 1 and first == second          # the second call comes from the cache
    assert "CIRCLE('ICRS', 269.446270, 4.768190, 0.16500)" in calls[0]
    star, faint = first["stars"]
    assert star["id"] == "4472832130942575872" and star["pmdec"] == 10362.39
    assert (faint["pmra"], faint["pmdec"], faint["parallax"]) == (0.0, 0.0, None)   # missing motion -> none
    assert first["epoch"] == 2016.0


def test_difference_cancels_still_stars_and_shows_a_mover():
    from PIL import Image

    yy, xx = np.mgrid[:60, :60]

    def star(x, y, peak=10.0):
        return peak * np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / 4)

    def visit(season, mover_x):
        return {"id": f"season-{season}", "season": season, "image": (star(15, 15) + star(mover_x, 40)).astype("f4"),
                "n_exposures": 10, "time_start": "a", "time_end": "b"}

    diff = pipeline.difference(visit(1, 36), visit(0, 30))
    image = diff["image"]
    assert abs(image[15, 15]) < 1e-5                 # the still star cancels
    assert image[40, 36] > 5 and image[40, 30] < -5  # bright where the mover is now, dark where it was
    assert diff["n_exposures"] == 20 and diff["minus"]["season"] == 0 and diff["season"] == 1

    image[0, 0] = np.nan
    pixels = np.array(Image.open(io.BytesIO(render.to_png_signed(image, 12.0, 2.0))))
    assert pixels[59 - 15, 15] in (127, 128)         # no change is mid-grey (rows are flipped)
    assert pixels[59 - 40, 36] > 200 and pixels[59 - 40, 30] < 55
    assert pixels[59, 0] in (127, 128)               # no data is mid-grey too


def test_flag_fractions():
    flags = np.zeros((10, 10), "i4")
    flags[:5] |= 1 << prepare.FLAG_BITS["SOURCE"]
    flags[0, 0] |= 1 << prepare.FLAG_BITS["HOT"]
    assert prepare.flag_fractions(flags) == {"HOT": 0.01, "SOURCE": 0.5}


def test_name_lookup_moves_a_fast_star_to_the_given_date():
    from app import resolve

    xml = """<Sesame><Target><name>Barnard's Star</name><Resolver name="Sc=Simbad">
      <jradeg>269.45207696</jradeg><jdedeg>4.69336497</jdedeg>
      <pm><v>10393.349</v><pmRA>-801.551</pmRA><epmRA>0.032</epmRA><pmDE>10362.394</pmDE></pm>
    </Resolver></Target></Sesame>"""
    found = resolve.move_to(resolve.parse_sesame(xml), 2026.0)
    assert found["ra"] == pytest.approx(269.44627, abs=2e-5) and found["dec"] == pytest.approx(4.76820, abs=2e-5)
    assert found["moved_arcsec"] == pytest.approx(270.2, abs=0.2)

    galaxy = resolve.move_to(resolve.parse_sesame("<jradeg>10.6847</jradeg><jdedeg>41.2690</jdedeg>"), 2026.0)
    assert (galaxy["ra"], galaxy["dec"], galaxy["moved_arcsec"]) == (10.6847, 41.269, 0.0)

    with pytest.raises(resolve.NotFound):
        resolve.parse_sesame("<Sesame><Target><INFO>Nothing found</INFO></Target></Sesame>")
