"""
Document loader for various file formats.
Based on working-demo implementation.
"""
import csv
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def load_document(file_path: str, brand: Optional[str] = None) -> List[Dict]:
    """
    Load a document and return a list of document chunks.
    
    Args:
        file_path: Path to the document
        brand: Optional brand name (required for non-CSV files)
        
    Returns:
        List of document dicts with 'text' and 'brand' keys
    """
    file_path_obj = Path(file_path)
    
    if not file_path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    ext = file_path_obj.suffix.lower()
    
    if ext == '.csv':
        return _load_csv(file_path, brand=brand)
    elif ext in ['.xlsx', '.xls']:
        return _load_excel(file_path, brand=brand)
    elif ext == '.txt':
        return _load_text(file_path, brand)
    elif ext == '.pdf':
        return _load_pdf(file_path, brand)
    elif ext == '.docx':
        return _load_docx(file_path, brand)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def _load_csv(file_path: str, brand: Optional[str] = None) -> List[Dict]:
    """Load CSV file with BrandKey and Description columns (required)."""
    documents = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        
        # Check for required columns (case-insensitive, handle various formats)
        brand_key_col = None
        desc_col = None

        for col in fieldnames:
            col_lower = col.lower().strip()
            # Handle BrandKey variations
            if col_lower in ['brandkey', 'brand_key', 'brand key', 'brand', 'brandkey', 'brand_key', 'brand key']:
                brand_key_col = col
            # Handle Description variations
            elif col_lower in ['description', 'desc', 'brand dna response', 'brand_dna_response', 'dna response', 'dna_response', 'response', 'brand dna', 'brand_dna', 'dna']:
                desc_col = col
        
        if not brand_key_col:
            raise ValueError(
                f"CSV file must have a 'BrandKey' column. Found columns: {', '.join(fieldnames)}"
            )
        if not desc_col:
            raise ValueError(
                f"CSV file must have a 'Description' column. Found columns: {', '.join(fieldnames)}"
            )
        
        # Use provided brand name, or require it
        if not brand:
            raise ValueError(
                "Brand name is required. Please provide a brand name when uploading the file."
            )
        
        for row in reader:
            brand_key = row.get(brand_key_col, '').strip()
            description = row.get(desc_col, '').strip()
            
            if not brand_key:
                logger.warning(f"Empty BrandKey in row, skipping")
                continue
            if not description:
                logger.warning(f"Empty Description for brand key '{brand_key}', skipping")
                continue
            
            # Use the provided brand name for all documents
            documents.append({
                'text': f"{brand_key}: {description}",  # Include brand key in text for context
                'brand': brand
            })
    
    logger.info(f"Loaded {len(documents)} documents from CSV for brand: {brand}")
    return documents


def _load_excel(file_path: str, brand: Optional[str] = None) -> List[Dict]:
    """Load Excel file with BrandKey and Description columns (required)."""
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas is required to load Excel files")
    
    df = pd.read_excel(file_path)
    documents = []
    
    # Check for required columns (case-insensitive, handle various formats)
    brand_key_col = None
    desc_col = None

    for col in df.columns:
        col_lower = str(col).lower().strip()
        # Handle BrandKey variations
        if col_lower in ['brandkey', 'brand_key', 'brand key', 'brand', 'brandkey', 'brand_key', 'brand key']:
            brand_key_col = col
        # Handle Description variations
        elif col_lower in ['description', 'desc', 'brand dna response', 'brand_dna_response', 'dna response', 'dna_response', 'response', 'brand dna', 'brand_dna', 'dna']:
            desc_col = col
    
    if not brand_key_col:
        raise ValueError(
            f"Excel file must have a 'BrandKey' column. Found columns: {', '.join(df.columns.tolist())}"
        )
    if not desc_col:
        raise ValueError(
            f"Excel file must have a 'Description' column. Found columns: {', '.join(df.columns.tolist())}"
        )
    
    # Use provided brand name, or require it
    if not brand:
        raise ValueError(
            "Brand name is required. Please provide a brand name when uploading the file."
        )
        
    for _, row in df.iterrows():
        brand_key = str(row.get(brand_key_col, '')).strip()
        description = str(row.get(desc_col, '')).strip()
        
        if pd.isna(row.get(brand_key_col)) or not brand_key:
            logger.warning(f"Empty BrandKey in row, skipping")
            continue
        if pd.isna(row.get(desc_col)) or not description:
            logger.warning(f"Empty Description for brand key '{brand_key}', skipping")
            continue
        
        # Use the provided brand name for all documents
        documents.append({
            'text': f"{brand_key}: {description}",  # Include brand key in text for context
            'brand': brand
        })
    
    logger.info(f"Loaded {len(documents)} documents from Excel for brand: {brand}")
    return documents


def _load_text(file_path: str, brand: str) -> List[Dict]:
    """Load plain text file."""
    if not brand:
        raise ValueError("Brand name is required for text files")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    return [{
        'text': text,
        'brand': brand
    }]


def _load_pdf(file_path: str, brand: str) -> List[Dict]:
    """Load PDF file."""
    if not brand:
        raise ValueError("Brand name is required for PDF files")
    
    try:
        import PyPDF2
    except ImportError:
        raise ImportError("PyPDF2 is required to load PDF files")
    
    text_parts = []
    
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text_parts.append(page.extract_text())
    
    text = "\n\n".join(text_parts)
    
    return [{
        'text': text,
        'brand': brand
    }]


def _load_docx(file_path: str, brand: str) -> List[Dict]:
    """Load DOCX file."""
    if not brand:
        raise ValueError("Brand name is required for DOCX files")
    
    try:
        from docx import Document
    except ImportError:
        raise ImportError("python-docx is required to load DOCX files")
    
    doc = Document(file_path)
    text_parts = [para.text for para in doc.paragraphs if para.text.strip()]
    text = "\n\n".join(text_parts)
    
    return [{
        'text': text,
        'brand': brand
    }]


def get_available_columns(file_path: str) -> List[str]:
    """Get available columns from a CSV or Excel file."""
    file_path_obj = Path(file_path)
    ext = file_path_obj.suffix.lower()
    
    if ext == '.csv':
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader.fieldnames)
    elif ext in ['.xlsx', '.xls']:
        import pandas as pd
        df = pd.read_excel(file_path, nrows=0)
        return list(df.columns)
    else:
        return []
