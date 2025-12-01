"""
================================================================================
Label Generation Service - PDF Shipping Labels
================================================================================
Version: 1.0.0
Created: 2025-12-01

Description:
    Service for generating printable PDF shipping labels from order data
    - Supports custom fonts and dimensions
    - Auto text wrapping and sizing
    - Batch processing (25 labels per PDF)
    - ZIP file creation for multiple PDFs

Dependencies:
    - reportlab: PDF generation
    - pandas: Data processing
    - openpyxl: Excel file reading

================================================================================
"""

import io
import zipfile
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
import logging

import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth

logger = logging.getLogger(__name__)


# ============================================================================
# Constants
# ============================================================================

DEFAULT_WIDTH_MM = 50
DEFAULT_HEIGHT_MM = 30
FONT_ADJUSTMENT = 2
MIN_SPACING_RATIO = 0.1
LABELS_PER_PDF = 25

AVAILABLE_FONTS = [
    "Courier-Bold",
    "Helvetica",
    "Helvetica-Bold",
    "Times-Roman",
    "Times-Bold",
    "Courier"
]


# ============================================================================
# Label Service
# ============================================================================

class LabelService:
    """Service for generating PDF shipping labels"""
    
    @staticmethod
    async def preview_labels(file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Parse uploaded file and return preview data
        
        Args:
            file_content: File bytes
            filename: Original filename
            
        Returns:
            Dict with preview data, stats, and validation info
            
        Raises:
            ValueError: If file format invalid or missing required columns
        """
        try:
            # Parse file based on extension
            if filename.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(file_content))
            elif filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
            else:
                raise ValueError("Unsupported file format. Please upload CSV or Excel file.")
            
            # Normalize column names
            df.columns = [col.strip().lower() for col in df.columns]
            
            # Validate required columns
            required_cols = ['order #', 'name']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                available_cols = df.columns.tolist()
                raise ValueError(
                    f"Missing required columns: {', '.join(missing_cols)}. "
                    f"Available columns: {', '.join(available_cols)}"
                )
            
            # Track original count
            total_entries = len(df)
            
            # Clean data
            df['order #'] = df['order #'].astype(str).str.strip()
            df['name'] = df['name'].astype(str).str.strip()
            
            # Remove duplicates
            before_dedup = len(df)
            df = df.drop_duplicates(subset=['order #', 'name'], keep='first')
            duplicates_removed = before_dedup - len(df)
            
            # Remove empty rows
            df = df[(df['order #'] != '') & (df['name'] != '')]
            
            if df.empty:
                raise ValueError("No valid data found after cleaning. Please check your file.")
            
            # Prepare preview data (first 20 rows)
            preview_data = df[['order #', 'name']].head(20).to_dict('records')
            
            return {
                'total_entries': total_entries,
                'duplicates_removed': duplicates_removed,
                'valid_labels': len(df),
                'preview_data': preview_data,
                'columns': df.columns.tolist(),
                'all_data': df[['order #', 'name']].to_dict('records')  # For generation
            }
            
        except Exception as e:
            logger.error(f"Error previewing labels: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to process file: {str(e)}")
    
    @staticmethod
    async def generate_labels(
        data: List[Dict[str, str]],
        font_name: str = "Courier-Bold",
        font_adjustment: int = 0,
        width_mm: int = DEFAULT_WIDTH_MM,
        height_mm: int = DEFAULT_HEIGHT_MM
    ) -> Tuple[bytes, str, bool]:
        """
        Generate PDF labels or ZIP file with multiple PDFs
        
        Args:
            data: List of dicts with 'order #' and 'name'
            font_name: Font to use
            font_adjustment: Font size adjustment (-5 to +5)
            width_mm: Label width in mm
            height_mm: Label height in mm
            
        Returns:
            Tuple of (file_bytes, filename, is_zip)
        """
        try:
            total_labels = len(data)
            
            # Validate font
            if font_name not in AVAILABLE_FONTS:
                font_name = "Courier-Bold"
            
            # Single PDF if <= 25 labels
            if total_labels <= LABELS_PER_PDF:
                pdf_bytes = LabelService._create_pdf(
                    data, font_name, font_adjustment, width_mm, height_mm
                )
                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                filename = f"labels_{timestamp}.pdf"
                return pdf_bytes, filename, False
            
            # Multiple PDFs in ZIP if > 25 labels
            else:
                zip_bytes = LabelService._create_zip(
                    data, font_name, font_adjustment, width_mm, height_mm
                )
                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                filename = f"labels_{timestamp}.zip"
                return zip_bytes, filename, True
                
        except Exception as e:
            logger.error(f"Error generating labels: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def _create_pdf(
        data: List[Dict[str, str]],
        font_name: str,
        font_adjustment: int,
        width_mm: int,
        height_mm: int
    ) -> bytes:
        """Create a single PDF with labels"""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=(width_mm * mm, height_mm * mm))
        
        for item in data:
            order_no = str(item.get('order #', ''))
            customer_name = str(item.get('name', ''))
            
            LabelService._draw_label(
                c, order_no, customer_name,
                font_name, width_mm * mm, height_mm * mm, font_adjustment
            )
            c.showPage()
        
        c.save()
        buffer.seek(0)
        return buffer.getvalue()
    
    @staticmethod
    def _create_zip(
        data: List[Dict[str, str]],
        font_name: str,
        font_adjustment: int,
        width_mm: int,
        height_mm: int
    ) -> bytes:
        """Create ZIP file with multiple PDFs (25 labels each)"""
        zip_buffer = io.BytesIO()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Split data into batches
            total_labels = len(data)
            num_batches = (total_labels + LABELS_PER_PDF - 1) // LABELS_PER_PDF
            
            for batch_num in range(num_batches):
                start_idx = batch_num * LABELS_PER_PDF
                end_idx = min(start_idx + LABELS_PER_PDF, total_labels)
                batch_data = data[start_idx:end_idx]
                
                # Create PDF for this batch
                pdf_bytes = LabelService._create_pdf(
                    batch_data, font_name, font_adjustment, width_mm, height_mm
                )
                
                # Add to ZIP
                batch_filename = f"labels_{timestamp}_batch{batch_num + 1}_({start_idx + 1}-{end_idx}).pdf"
                zip_file.writestr(batch_filename, pdf_bytes)
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
    
    @staticmethod
    def _draw_label(
        c: canvas.Canvas,
        order_no: str,
        customer_name: str,
        font_name: str,
        width: float,
        height: float,
        font_override: int = 0
    ):
        """Draw a single label on the canvas"""
        order_no_text = f"#{order_no.strip()}"
        customer_name_text = customer_name.strip().upper()
        
        # Calculate sections
        min_spacing = height * MIN_SPACING_RATIO
        half_height = (height - min_spacing) / 2
        
        # === Order # Section (top) ===
        order_lines = [order_no_text]
        order_font_size = LabelService._find_max_font_size(
            order_lines, width, half_height, font_name
        )
        order_font_size = max(order_font_size - FONT_ADJUSTMENT + font_override, 1)
        
        c.setFont(font_name, order_font_size)
        wrapped_order = []
        for line in order_lines:
            wrapped_order.extend(
                LabelService._wrap_text(line, font_name, order_font_size, width)
            )
        
        total_height_order = len(wrapped_order) * order_font_size + (len(wrapped_order) - 1) * 2
        start_y_order = height - half_height + (half_height - total_height_order) / 2
        
        for i, line in enumerate(wrapped_order):
            x = (width - stringWidth(line, font_name, order_font_size)) / 2
            y = start_y_order + (len(wrapped_order) - i - 1) * (order_font_size + 2)
            c.drawString(x, y, line)
        
        # === Horizontal Line ===
        line_y = half_height + min_spacing / 2
        c.setLineWidth(0.5)
        c.line(2, line_y, width - 2, line_y)
        
        # === Customer Name Section (bottom) ===
        words = customer_name_text.split()
        cust_lines = words if len(words) == 2 else [customer_name_text]
        
        line_font_sizes = []
        for line in cust_lines:
            max_height_per_line = half_height / len(cust_lines)
            fs = LabelService._find_max_font_size([line], width, max_height_per_line, font_name)
            fs = max(fs - FONT_ADJUSTMENT + font_override, 1)
            line_font_sizes.append(fs)
        
        total_height_cust = sum(line_font_sizes) + 2 * (len(cust_lines) - 1)
        start_y_cust = (half_height - total_height_cust) / 2
        
        for i, line in enumerate(cust_lines):
            fs = line_font_sizes[i]
            c.setFont(font_name, fs)
            x = (width - stringWidth(line, font_name, fs)) / 2
            y = start_y_cust + (len(cust_lines) - i - 1) * (fs + 2)
            c.drawString(x, y, line)
    
    @staticmethod
    def _wrap_text(text: str, font_name: str, font_size: int, max_width: float) -> List[str]:
        """Wrap text into multiple lines that fit within max_width"""
        words = text.split()
        if not words:
            return [""]
        
        lines = []
        current_line = words[0]
        
        for word in words[1:]:
            test_line = f"{current_line} {word}"
            if stringWidth(test_line, font_name, font_size) <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        
        lines.append(current_line)
        return lines
    
    @staticmethod
    def _find_max_font_size(
        lines: List[str],
        max_width: float,
        max_height: float,
        font_name: str
    ) -> int:
        """Find maximum font size that fits text within dimensions using binary search"""
        low = 1
        high = 200  # Reasonable max font size
        best_size = 1
        
        while low <= high:
            mid = (low + high) // 2
            
            # Check if this font size fits
            fits = True
            wrapped_lines = []
            for line in lines:
                wrapped_lines.extend(
                    LabelService._wrap_text(line, font_name, mid, max_width)
                )
            
            total_height = len(wrapped_lines) * mid + (len(wrapped_lines) - 1) * 2
            
            # Check width of all lines
            for line in wrapped_lines:
                if stringWidth(line, font_name, mid) > (max_width - 4):
                    fits = False
                    break
            
            # Check height
            if fits and total_height > (max_height - 4):
                fits = False
                
            if fits:
                best_size = mid
                low = mid + 1
            else:
                high = mid - 1
                
        return best_size
