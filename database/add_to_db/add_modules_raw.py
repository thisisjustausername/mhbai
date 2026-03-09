from ai.overall_ai.full_extraction import load_pdf_modules

def add_modules_raw_to_db() -> None:
    """
    Add raw modules extracted from PDFs to the database.
    """
    load_pdf_modules(pdf_folder="~/mhbai/pdfs/", from_db=False, save_path="", remove_duplicates=False)

if __name__ == "__main__":
    add_modules_raw_to_db()