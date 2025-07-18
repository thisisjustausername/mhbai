from pdfrw import PdfWriter, PdfDict, PdfName, PdfObject

# creating pdf out of the string

with open("part_of_pdf.txt", "r") as file:
    text = file.read()

content_stream = PdfDict(
    stream=text.encode('utf-8')
)

# Create a simple page dictionary
page = PdfDict(
    Type=PdfName.Page,
    MediaBox=[0, 0, 595, 842],  # A4 size
    Contents=content_stream,
    Resources=PdfDict(
        Font=PdfDict(
            F3=PdfDict(
                Type=PdfName.Font,
                Subtype=PdfName.Type1,
                BaseFont=PdfName.Helvetica  # assuming Helvetica for /F3
            )
        )
    )
)

# Create the PDF root and catalog
root = PdfDict(
    Type=PdfName.Catalog,
    Pages=PdfDict(
        Type=PdfName.Pages,
        Count=1,
        Kids=[page]
    )
)

# Write PDF file
writer = PdfWriter()
writer.trailer = root
writer.write("output.pdf")