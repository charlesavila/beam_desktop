"""Small dependency-free PDF calculation sheet exporter."""
import math

from .models import PointLoad


PAGE_W, PAGE_H = 612, 792


def _number(value, digits=3):
    if not math.isfinite(value):
        return "n/a"
    return f"{value:.{digits}f}"


def _load_text(load, index):
    if isinstance(load, PointLoad):
        return f"{index}. Point: {load.magnitude:g} kips at {load.position:g} ft"
    return f"{index}. Uniform: {load.magnitude:g} kip/ft from {load.start:g} to {load.end:g} ft"


class Page:
    def __init__(self):
        self.ops = []

    @staticmethod
    def _f(value):
        return f"{value:.2f}"

    def text(self, x, y, value, size=10, bold=False):
        value = str(value).encode("ascii", "replace").decode("ascii")
        value = value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        font = "F2" if bold else "F1"
        self.ops.append(f"BT /{font} {size} Tf {self._f(x)} {self._f(y)} Td ({value}) Tj ET")

    def line(self, x1, y1, x2, y2, width=1, gray=0.2):
        self.ops.append(f"{gray:.2f} G {width:.2f} w {self._f(x1)} {self._f(y1)} m "
                        f"{self._f(x2)} {self._f(y2)} l S 0 G")

    def polyline(self, points, width=1.6, gray=0.18):
        if len(points) < 2:
            return
        commands = [f"{gray:.2f} G {width:.2f} w {self._f(points[0][0])} {self._f(points[0][1])} m"]
        commands.extend(f"{self._f(x)} {self._f(y)} l" for x, y in points[1:])
        commands.append("S 0 G")
        self.ops.append(" ".join(commands))

    def rect(self, x, y, width, height, gray=0.78):
        self.ops.append(f"{gray:.2f} G 0.7 w {self._f(x)} {self._f(y)} {self._f(width)} {self._f(height)} re S 0 G")

    def header(self, title, subtitle):
        self.text(40, 754, title, 19, True)
        self.text(40, 736, subtitle, 9)
        self.line(40, 724, 572, 724, 1, 0.62)

    def footer(self, page_number, total):
        self.line(40, 35, 572, 35, 0.6, 0.72)
        self.text(40, 21, "Beam Designer | Calculation sheet", 8)
        self.text(523, 21, f"Page {page_number} of {total}", 8)

    def chart(self, x, y, width, height, title, unit, samples, attribute, span):
        self.text(x, y + height - 3, f"{title} ({unit})", 12, True)
        left, right = x + 55, x + width - 12
        bottom, top = y + 27, y + height - 24
        values = [getattr(sample, attribute) for sample in samples]
        low, high = min([0.0] + values), max([0.0] + values)
        if math.isclose(low, high, abs_tol=1e-14):
            low, high = -1.0, 1.0
        pad = (high - low) * 0.08
        low, high = low - pad, high + pad
        to_x = lambda value: left + (right-left) * value / span
        to_y = lambda value: bottom + (top-bottom) * (value-low) / (high-low)
        self.line(left, bottom, left, top, 0.7, 0.45)
        self.line(left, to_y(0), right, to_y(0), 0.7, 0.45)
        self.line(left, bottom, right, bottom, 0.7, 0.45)
        self.text(x, top-3, _number(high, 2), 8)
        self.text(x, bottom-2, _number(low, 2), 8)
        self.text(left, y+11, "0 ft", 8)
        self.text(right-32, y+11, f"{span:g} ft", 8)
        pts = [(to_x(sample.x), to_y(getattr(sample, attribute))) for sample in samples]
        self.polyline(pts, 1.7, 0.22)


def _beam_diagram(page, beam, x, y, width, height):
    page.text(x, y + height - 2, "Beam and loading", 12, True)
    left, right = x + 22, x + width - 20
    beam_y = y + 74
    map_x = lambda position: left + (right-left) * position / beam.span
    page.line(left, beam_y, right, beam_y, 5, 0.2)
    if beam.support == "Cantilever":
        page.line(left-4, beam_y-24, left-4, beam_y+24, 2, 0.22)
        for offset in range(-22, 24, 8):
            page.line(left-12, beam_y+offset, left-4, beam_y+offset+8, 0.7, 0.5)
        page.text(left-7, beam_y-39, "Fixed", 8)
    else:
        for sx, label in ((left, "Pin"), (right, "Roller")):
            page.polyline(((sx-10, beam_y-17), (sx+10, beam_y-17), (sx, beam_y-3), (sx-10, beam_y-17)), 0.8)
            page.line(sx-13, beam_y-20, sx+13, beam_y-20, 0.7, 0.4)
            page.text(sx-10, beam_y-36, label, 8)
    for i, load in enumerate(beam.loads):
        if isinstance(load, PointLoad):
            px = map_x(load.position)
            top = beam_y + 47
            page.line(px, top, px, beam_y+6, 1, 0.27)
            page.polyline(((px-3, beam_y+12), (px, beam_y+6), (px+3, beam_y+12)), 1, 0.27)
            page.text(min(max(px-26, left), right-62), top+3, f"P{i+1}: {load.magnitude:g} k", 8)
        else:
            sx, ex = map_x(load.start), map_x(load.end)
            top = beam_y + 43
            page.line(sx, top, ex, top, 1, 0.28)
            page.text(min(max(sx, left), right-78), top+5, f"w: {load.magnitude:g} k/ft", 8)
            count = max(2, min(12, int((ex-sx)/24)+1))
            for j in range(count):
                px = sx + (ex-sx) * j / (count-1)
                page.line(px, top-2, px, beam_y+6, 0.8, 0.3)
                page.polyline(((px-2.5, beam_y+11), (px, beam_y+6), (px+2.5, beam_y+11)), 0.8, 0.3)
    page.text(left, y+18, "0 ft", 8)
    page.text(right-26, y+18, f"{beam.span:g} ft", 8)


def _cover_page(beam, result, section, material, first_load, last_load):
    page = Page()
    page.header("Beam Calculation Sheet", "Design inputs, analysis summary, and checks")
    page.text(40, 702, "Inputs", 13, True)
    rows = [
        ("Support", beam.support),
        ("Span", f"{beam.span:g} ft"),
        ("Section", section),
        ("Material", material),
        ("Moment of inertia, I", f"{beam.properties.inertia:g} in^4"),
        ("Section modulus, S", f"{beam.properties.section_modulus:g} in^3"),
        ("Elastic modulus, E", f"{beam.properties.elasticity:g} ksi"),
        ("Allowable bending stress, Fb", f"{beam.properties.allowable_stress:g} ksi"),
        ("Deflection limit", f"{result.deflection_limit:.3f} in (L/360)"),
    ]
    y = 681
    for label, value in rows:
        page.text(45, y, label, 9)
        page.text(205, y, value, 9, True)
        y -= 17
    page.text(40, y-2, "Loads", 11, True)
    y -= 20
    load_end = min(last_load, len(beam.loads))
    if first_load >= load_end:
        page.text(45, y, "No applied loads", 9)
    else:
        for idx in range(first_load, load_end):
            page.text(45, y, _load_text(beam.loads[idx], idx+1), 8.5)
            y -= 14

    page.text(340, 702, "Results and checks", 13, True)
    values = [
        ("Left reaction", f"{result.left_reaction:.3f} kips up"),
        ("Right reaction", f"{result.right_reaction:.3f} kips up"),
        ("Fixed-end moment", f"{result.fixed_moment:.3f} kip-ft"),
        ("Maximum |shear|", f"{abs(result.max_shear.value):.3f} kips at {result.max_shear.location:.3f} ft"),
        ("Governing |moment|", f"{abs(result.governing_moment.value):.3f} kip-ft at {result.governing_moment.location:.3f} ft"),
        ("Maximum |deflection|", f"{abs(result.max_deflection.value):.3f} in at {result.max_deflection.location:.3f} ft"),
    ]
    y = 681
    for label, value in values:
        page.text(345, y, label, 9)
        page.text(345, y-13, value, 8.5, True)
        y -= 34
    page.text(345, y-2, f"Bending check: {'PASS' if result.bending_pass else 'FAIL'}", 10, True)
    page.text(345, y-17, f"{result.stress:.3f} ksi / {beam.properties.allowable_stress:.3f} ksi allowable", 8.5)
    page.text(345, y-43, f"Deflection check: {'PASS' if result.deflection_pass else 'FAIL'}", 10, True)
    page.text(345, y-58, f"{abs(result.max_deflection.value):.3f} in / {result.deflection_limit:.3f} in limit", 8.5)
    page.line(320, 690, 320, 365, 0.6, 0.8)
    page.line(40, 365, 572, 365, 0.8, 0.7)
    page.text(40, 345, "Checks use unrounded analysis values; displayed values are rounded for reporting.", 8)
    return page


def _diagram_page_one(beam, result):
    page = Page()
    page.header("Analysis Diagrams", "Beam loading and shear diagram")
    _beam_diagram(page, beam, 48, 418, 516, 278)
    page.rect(42, 408, 528, 286)
    page.chart(48, 62, 516, 320, "Shear diagram", "kips", result.samples, "shear", beam.span)
    return page


def _diagram_page_two(beam, result):
    page = Page()
    page.header("Analysis Diagrams", "Moment and deflection diagrams")
    page.chart(48, 414, 516, 282, "Moment diagram", "kip-ft", result.samples, "moment", beam.span)
    page.rect(42, 405, 528, 291)
    page.chart(48, 65, 516, 282, "Deflection diagram", "in", result.samples, "deflection", beam.span)
    page.rect(42, 56, 528, 291)
    return page


def _pdf_bytes(pages):
    objects = [b""]
    def add(data):
        objects.append(data)
        return len(objects)-1

    font_regular = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    font_bold = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
    page_ids, content_ids = [], []
    for page in pages:
        stream = "\n".join(page.ops).encode("ascii")
        content_ids.append(add(b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream"))
        page_ids.append(add(b""))
    pages_id = add(b"")
    for page_id, content_id in zip(page_ids, content_ids):
        objects[page_id] = (f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {PAGE_W} {PAGE_H}] "
                            f"/Resources << /Font << /F1 {font_regular} 0 R /F2 {font_bold} 0 R >> >> "
                            f"/Contents {content_id} 0 R >>").encode("ascii")
    objects[pages_id] = (f"<< /Type /Pages /Kids [{' '.join(f'{i} 0 R' for i in page_ids)}] "
                         f"/Count {len(page_ids)} >>").encode("ascii")
    catalog_id = add(f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode("ascii"))
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, obj in enumerate(objects[1:], 1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode("ascii"))
        output.extend(obj)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects)}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(f"trailer\n<< /Size {len(objects)} /Root {catalog_id} 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii"))
    return bytes(output)


def export_calculation_sheet(path, beam, result, section, material):
    """Write a multi-page, vector PDF calculation sheet."""
    pages = [_cover_page(beam, result, section, material, 0, min(len(beam.loads), 10))]
    remaining = len(beam.loads) - min(len(beam.loads), 10)
    start = 10
    while remaining:
        page = Page()
        page.header("Calculation Sheet - Input Continuation", "Applied loads")
        end = min(len(beam.loads), start + 42)
        for idx in range(start, end):
            col, row = (0, idx-start) if idx-start < 21 else (1, idx-start-21)
            page.text(45 + col*270, 690 - row*27, _load_text(beam.loads[idx], idx+1), 8.5)
        pages.append(page)
        start, remaining = end, len(beam.loads)-end
    pages.extend((_diagram_page_one(beam, result), _diagram_page_two(beam, result)))
    total = len(pages)
    for number, page in enumerate(pages, 1):
        page.footer(number, total)
    with open(path, "wb") as pdf_file:
        pdf_file.write(_pdf_bytes(pages))
