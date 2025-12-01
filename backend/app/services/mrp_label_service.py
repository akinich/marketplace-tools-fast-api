"""
================================================================================
MRP Label Service - PDF Merging & Management
================================================================================
Version: 1.0.0
Created: 2025-12-01

Description:
    Service for merging multiple product label PDFs based on Excel quantity data.
    Also handles management of source PDFs in Supabase Storage.

Dependencies:
    - pypdf: PDF merging
    - pandas: Data processing
    - supabase: Cloud storage
"""

import io
import zipfile
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
import logging
import pandas as pd
from pypdf import PdfWriter, PdfReader

from app.utils.supabase_client import get_supabase_client_async

logger = logging.getLogger(__name__)

# Constants
BUCKET_NAME = 'mrp_labels'
MAX_FILE_SIZE_MB = 10
MAX_DECOMPRESSED_SIZE_MB = 100
LABELS_PER_FILE = 25

class MrpLabelService:
    """Service for MRP label PDF merging and library management"""
    
    @staticmethod
    async def validate_excel(file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Validate and parse uploaded Excel file
        
        Returns:
            Dict with parsed data and validation info
        """
        try:
            # 1. Basic validation
            if not filename.endswith(('.xlsx', '.xls')):
                raise ValueError("Invalid file type. Only .xlsx and .xls allowed.")
            
            # 2. Security check (zip bomb for xlsx)
            if filename.endswith('.xlsx'):
                try:
                    with zipfile.ZipFile(io.BytesIO(file_content)) as zf:
                        total_size = sum(info.file_size for info in zf.infolist())
                        if total_size > MAX_DECOMPRESSED_SIZE_MB * 1024 * 1024:
                            raise ValueError("File decompression size too large (potential zip bomb)")
                except zipfile.BadZipFile:
                    raise ValueError("Invalid Excel file (corrupt ZIP structure)")

            # 3. Parse Excel
            try:
                xls = pd.ExcelFile(io.BytesIO(file_content))
                if "Item Summary" not in xls.sheet_names:
                    raise ValueError("Sheet 'Item Summary' not found")
                
                df = pd.read_excel(xls, sheet_name="Item Summary")
            except Exception as e:
                raise ValueError(f"Failed to read Excel data: {str(e)}")

            # 4. Validate Columns
            # Normalize columns
            df.columns = [str(col).strip().lower() for col in df.columns]
            
            # Map aliases
            col_map = {}
            aliases = {
                'item_id': ['item id', 'itemid', 'item', 'product_id'],
                'variation_id': ['variation id', 'variationid', 'variation'],
                'quantity': ['quantity', 'qty', 'count', 'copies']
            }
            
            for standard, alias_list in aliases.items():
                for col in df.columns:
                    if col in alias_list:
                        col_map[standard] = col
                        break
            
            missing = [k for k in aliases.keys() if k not in col_map]
            if missing:
                raise ValueError(f"Missing required columns: {', '.join(missing)}")
            
            # 5. Clean Data
            df = df.rename(columns={v: k for k, v in col_map.items()})
            df = df[['item_id', 'variation_id', 'quantity']]
            
            # Convert to numeric
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            
            # Filter valid rows
            df = df[df['quantity'] > 0]
            df = df[(df['item_id'] > 0) | (df['variation_id'] > 0)]
            
            if df.empty:
                raise ValueError("No valid data rows found")
            
            # 6. Check PDF Availability
            supabase = await get_supabase_client_async()
            files = supabase.storage.from_(BUCKET_NAME).list()
            available_files = {f['name'] for f in files}
            
            data_rows = []
            missing_pdfs = set()
            total_pages = 0
            
            for _, row in df.iterrows():
                # Logic: Use variation_id if present, else item_id
                use_id = row['variation_id'] if row['variation_id'] != 0 else row['item_id']
                filename = f"{use_id}.pdf"
                
                if filename not in available_files:
                    missing_pdfs.add(filename)
                
                data_rows.append({
                    'item_id': int(row['item_id']),
                    'variation_id': int(row['variation_id']),
                    'quantity': int(row['quantity']),
                    'pdf_filename': filename,
                    'is_available': filename in available_files
                })
                
                if filename in available_files:
                    total_pages += row['quantity']
            
            return {
                'total_items': int(len(df)),
                'total_pages': int(total_pages),
                'valid_rows': int(len(data_rows)),
                'missing_pdfs': list(missing_pdfs),
                'data': data_rows
            }

        except Exception as e:
            logger.error(f"Error validating MRP Excel: {str(e)}", exc_info=True)
            raise ValueError(str(e))

    @staticmethod
    async def generate_merged_pdf(data: List[Dict[str, Any]]) -> Tuple[bytes, str, bool]:
        """
        Merge PDFs based on data
        
        Returns:
            Tuple(file_bytes, filename, is_zip)
        """
        try:
            supabase = await get_supabase_client_async()
            merger = PdfWriter()
            total_pages = 0
            
            # Cache downloaded PDFs to avoid repeated downloads
            pdf_cache = {}
            
            for item in data:
                if not item.get('is_available'):
                    continue
                    
                filename = item['pdf_filename']
                qty = item['quantity']
                
                # Download if not cached
                if filename not in pdf_cache:
                    try:
                        res = supabase.storage.from_(BUCKET_NAME).download(filename)
                        pdf_cache[filename] = io.BytesIO(res)
                    except Exception as e:
                        logger.error(f"Failed to download {filename}: {e}")
                        continue
                
                # Merge
                try:
                    src_pdf = PdfReader(pdf_cache[filename])
                    # We assume source PDF is 1 page. If multi-page, we append all pages.
                    # Usually labels are 1 page.
                    for _ in range(qty):
                        for page in src_pdf.pages:
                            merger.add_page(page)
                            total_pages += 1
                except Exception as e:
                    logger.error(f"Error merging {filename}: {e}")
            
            if total_pages == 0:
                raise ValueError("No valid PDFs to merge")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            
            # If small enough, return single PDF
            if total_pages <= LABELS_PER_FILE:
                out_buffer = io.BytesIO()
                merger.write(out_buffer)
                out_buffer.seek(0)
                return out_buffer.getvalue(), f"mrp_labels_{timestamp}.pdf", False
            
            # Else split and zip
            else:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                    # We need to split the merged pages
                    # Since PdfWriter doesn't support easy splitting of already merged content in memory efficiently without writing,
                    # we'll re-iterate or split the huge writer. 
                    # Actually, pypdf PdfWriter pages can be accessed.
                    
                    num_chunks = (total_pages + LABELS_PER_FILE - 1) // LABELS_PER_FILE
                    
                    for i in range(num_chunks):
                        chunk_writer = PdfWriter()
                        start = i * LABELS_PER_FILE
                        end = min(start + LABELS_PER_FILE, total_pages)
                        
                        for p_idx in range(start, end):
                            chunk_writer.add_page(merger.pages[p_idx])
                        
                        chunk_buf = io.BytesIO()
                        chunk_writer.write(chunk_buf)
                        zf.writestr(f"mrp_labels_part_{i+1}.pdf", chunk_buf.getvalue())
                
                zip_buffer.seek(0)
                return zip_buffer.getvalue(), f"mrp_labels_{timestamp}.zip", True

        except Exception as e:
            logger.error(f"Error generating merged PDF: {str(e)}", exc_info=True)
            raise

    @staticmethod
    async def list_library_pdfs() -> List[Dict[str, Any]]:
        """List all PDFs in library"""
        try:
            supabase = await get_supabase_client_async()
            files = supabase.storage.from_(BUCKET_NAME).list()
            
            # Sort by name (numeric aware if possible, but string sort is default)
            # We can try to sort numerically if names are numbers
            def sort_key(f):
                name = f['name'].replace('.pdf', '')
                return int(name) if name.isdigit() else name
                
            files.sort(key=sort_key)
            
            return [
                {
                    'name': f['name'],
                    'size': f['metadata'].get('size', 0),
                    'created_at': f['created_at'],
                    'updated_at': f['updated_at']
                }
                for f in files
            ]
        except Exception as e:
            logger.error(f"Error listing PDFs: {e}")
            raise

    @staticmethod
    async def upload_pdf(file_content: bytes, filename: str) -> Dict[str, Any]:
        """Upload PDF to library"""
        try:
            if not filename.lower().endswith('.pdf'):
                raise ValueError("Only PDF files allowed")
            
            supabase = await get_supabase_client_async()
            
            # Check if exists (to overwrite or error? Streamlit code implies overwrite or error handling)
            # Supabase upload with upsert=True is safest
            res = supabase.storage.from_(BUCKET_NAME).upload(
                filename,
                file_content,
                file_options={"content-type": "application/pdf", "upsert": "true"}
            )
            return {"message": "Upload successful", "filename": filename}
            
        except Exception as e:
            logger.error(f"Error uploading PDF {filename}: {e}")
            raise

    @staticmethod
    async def delete_pdf(filename: str) -> Dict[str, Any]:
        """Delete PDF from library"""
        try:
            supabase = await get_supabase_client_async()
            supabase.storage.from_(BUCKET_NAME).remove([filename])
            return {"message": "Deleted successfully"}
        except Exception as e:
            logger.error(f"Error deleting PDF {filename}: {e}")
            raise
