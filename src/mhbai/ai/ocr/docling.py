from docling.document_converter import DocumentConverter

source = "pdfs/1.pdf"
converter = DocumentConverter()
result = converter.convert(source)
print(result.document.export_to_markdown())  # output: "## Docling Technical Report[...]"

with open("test-docling.md", "w") as f:
    f.write(result.document.export_to_markdown())