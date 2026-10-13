"""Generate tests/fixtures/three_page.pdf (3 pages, one raster figure). Committed."""

import pymupdf

doc = pymupdf.open()
page1 = doc.new_page()
page1.insert_text(
    (72, 72),
    "Probability as a mathematical framework.\n\nSample space Omega lists all outcomes. "
    "The list must be mutually exclusive and collectively exhaustive.",
)
page2 = doc.new_page()
page2.insert_text((72, 72), "Venn diagrams show set relations between events A and B.")
pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 120, 80))
pix.set_rect(pix.irect, (200, 30, 40))
page2.insert_image(pymupdf.Rect(72, 120, 300, 220), pixmap=pix)
page3 = doc.new_page()
page3.insert_text((72, 72), "End of fixture.")
doc.save("tests/fixtures/three_page.pdf")
print("wrote tests/fixtures/three_page.pdf")
