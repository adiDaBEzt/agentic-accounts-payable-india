"""
Builds the 2-slide submission deck from the rendered HTML slides.

1. Start the app (uvicorn on :8080), then render each slide:
   Chrome --headless --window-size=1920,1080 --screenshot=frontend/slideN.png \
          "http://127.0.0.1:8080/presentation.html?only=N"
2. Run: python3 generate_presentation.py
"""
from pptx import Presentation
from pptx.util import Inches

OUTPUT_PPTX = "IBM_watsonx_Orchestrate_AP_Automation.pptx"
SLIDES = ["frontend/slide1.png", "frontend/slide2.png"]

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
for img in SLIDES:
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.shapes.add_picture(img, 0, 0, prs.slide_width, prs.slide_height)
prs.save(OUTPUT_PPTX)
print("Saved", OUTPUT_PPTX)
