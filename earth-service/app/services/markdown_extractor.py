from markitdown import MarkItDown


def extract_markdown(file_path: str) -> str:
    """
    Extract markdown from a file (PDF, DOCX, etc.) using the markitdown CLI.
    Returns the extracted markdown as a string.
    """
    try:
        md = MarkItDown(enable_plugins=False)
        result = md.convert(file_path)
        return result.text_content
    except Exception as e:
        raise RuntimeError(f"markitdown failed: {str(e)}") from e
