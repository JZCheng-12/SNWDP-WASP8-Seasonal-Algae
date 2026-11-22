"""Pack rendered slide PNGs into a PDF preview; the PPTX remains the editable source.

Usage: python build_presentation_preview.py RENDER_DIRECTORY OUTPUT_PDF
Requires reportlab. Render files must be named slide-01.png, slide-02.png, ...
"""
import sys
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

def main():
    folder, output = map(Path, sys.argv[1:3])
    images = sorted(folder.glob('slide-*.png'))
    if not images:
        raise SystemExit('No slide PNGs found')
    output.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output), pagesize=(960, 540), pageCompression=1)
    pdf.setTitle('南水北调中线 WASP8 课程汇报（预览）')
    for number, image in enumerate(images, 1):
        assert image.stem == f'slide-{number:02d}', 'Slide numbering must be contiguous'
        pdf.drawImage(ImageReader(str(image)), 0, 0, width=960, height=540)
        pdf.showPage()
    pdf.save()
    print(f'{len(images)} pages: {output}')

if __name__ == '__main__':
    main()
