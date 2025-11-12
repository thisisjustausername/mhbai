# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai and pdf_reader.
#
# For usage please contact the developer.

# Description: Tests functions to read text from PDFs using libraries
# Status: PROTOTYPING
# FileID: Re-te-0002

from PyPDF2 import PdfWriter
from PyPDF2 import PageObject
from PyPDF2.generic import (
    NameObject,
    DictionaryObject,
    StreamObject
)

# Paths
input_path = "pdf_part1.txt"  # Replace with your actual file path
output_path = "rendered_pdf_page.pdf"

# Create PDF writer
writer = PdfWriter()

# Create a blank A4-sized page (595.276 x 841.890 points)
page = PageObject.create_blank_page(width=595.276, height=841.890)

# Read the raw content stream (from your .txt file)
with open(input_path, "rb") as f:
    raw_stream_data = f.read()

# Create a StreamObject for the content
content_stream = StreamObject()
content_stream._data = raw_stream_data
content_stream_obj = writer._add_object(content_stream)

# Attach the content stream and font resources to the page
page[NameObject("/Contents")] = content_stream_obj
"""page[NameObject("/Resources")] = DictionaryObject({
    NameObject("/Font"): DictionaryObject({
        NameObject("/F1"): DictionaryObject({
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica")
        }),
        NameObject("/F3"): DictionaryObject({
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica-Bold")
        }),
        NameObject("/F5"): DictionaryObject({
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/ZapfDingbats")
        }),
        NameObject("/F2"): DictionaryObject({
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica-Oblique")
        }),
    }),
})"""

# Add the page to the PDF
writer.add_page(page)

# Write the final PDF to disk
with open(output_path, "wb") as out_file:
    writer.write(out_file)

print(f"PDF created at: {output_path}")
