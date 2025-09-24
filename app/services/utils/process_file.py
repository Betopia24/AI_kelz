import os
import tempfile
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
import fitz  # PyMuPDF for PDF operations (correct import, do not import frontend)

class FileProcessor:
    def __init__(self):
        """Initialize the file processor"""
        self.max_size_mb = 10
        self.max_pages = 10
        self.max_size_bytes = self.max_size_mb * 1024 * 1024
        
    def get_file_info(self, file_path):
        """Get file size and page count"""
        file_size = os.path.getsize(file_path)
        page_count = 0
        
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.pdf':
            try:
                # Use PyMuPDF for more reliable page counting
                doc = fitz.open(file_path)
                page_count = doc.page_count
                doc.close()
            except Exception as e:
                print(f"Error reading PDF: {e}")
                # Fallback to PyPDF2
                try:
                    with open(file_path, 'rb') as f:
                        reader = PdfReader(f)
                        page_count = len(reader.pages)
                except Exception as e2:
                    print(f"Error with PyPDF2: {e2}")
                    page_count = 1  # Assume single page if can't determine
        else:
            # For image files, assume single page
            page_count = 1
            
        return file_size, page_count
    
    def split_pdf_by_size(self, file_path, target_size_bytes):
        """Split PDF into chunks based on file size"""
        chunks = []
        temp_dir = tempfile.mkdtemp()
        
        try:
            doc = fitz.open(file_path)
            total_pages = doc.page_count
            
            current_chunk_pages = []
            chunk_num = 0
            
            for page_num in range(total_pages):
                current_chunk_pages.append(page_num)
                
                # Create temporary PDF with current pages to check size
                temp_pdf_path = os.path.join(temp_dir, f"temp_chunk_{chunk_num}.pdf")
                temp_doc = fitz.open()
                
                for p in current_chunk_pages:
                    temp_doc.insert_pdf(doc, from_page=p, to_page=p)
                
                temp_doc.save(temp_pdf_path)
                temp_doc.close()
                
                # Check if chunk exceeds size limit
                if os.path.getsize(temp_pdf_path) > target_size_bytes and len(current_chunk_pages) > 1:
                    # Remove last page and create chunk
                    current_chunk_pages.pop()
                    
                    final_chunk_path = os.path.join(temp_dir, f"chunk_{chunk_num}.pdf")
                    chunk_doc = fitz.open()
                    
                    for p in current_chunk_pages:
                        chunk_doc.insert_pdf(doc, from_page=p, to_page=p)
                    
                    chunk_doc.save(final_chunk_path)
                    chunk_doc.close()
                    chunks.append(final_chunk_path)
                    
                    # Start new chunk with current page
                    current_chunk_pages = [page_num]
                    chunk_num += 1
                
                os.remove(temp_pdf_path)
            
            # Handle remaining pages
            if current_chunk_pages:
                final_chunk_path = os.path.join(temp_dir, f"chunk_{chunk_num}.pdf")
                chunk_doc = fitz.open()
                
                for p in current_chunk_pages:
                    chunk_doc.insert_pdf(doc, from_page=p, to_page=p)
                
                chunk_doc.save(final_chunk_path)
                chunk_doc.close()
                chunks.append(final_chunk_path)
            
            doc.close()
            
        except Exception as e:
            print(f"Error splitting PDF by size: {e}")
            return [file_path]  # Return original file if splitting fails
        
        return chunks
    
    def split_pdf_by_pages(self, file_path, max_pages):
        """Split PDF into chunks based on page count"""
        chunks = []
        temp_dir = tempfile.mkdtemp()
        
        try:
            doc = fitz.open(file_path)
            total_pages = doc.page_count
            
            chunk_num = 0
            for start_page in range(0, total_pages, max_pages):
                end_page = min(start_page + max_pages - 1, total_pages - 1)
                
                chunk_path = os.path.join(temp_dir, f"chunk_{chunk_num}.pdf")
                chunk_doc = fitz.open()
                
                chunk_doc.insert_pdf(doc, from_page=start_page, to_page=end_page)
                chunk_doc.save(chunk_path)
                chunk_doc.close()
                
                chunks.append(chunk_path)
                chunk_num += 1
            
            doc.close()
            
        except Exception as e:
            print(f"Error splitting PDF by pages: {e}")
            return [file_path]  # Return original file if splitting fails
        
        return chunks
    
    def split_image_by_size(self, file_path, target_size_bytes):
        """Split image by reducing quality if it exceeds size limit"""
        chunks = []
        temp_dir = tempfile.mkdtemp()
        
        try:
            with Image.open(file_path) as img:
                # Calculate quality reduction needed
                current_size = os.path.getsize(file_path)
                
                if current_size <= target_size_bytes:
                    return [file_path]
                
                # Reduce quality to meet size requirement
                quality = int((target_size_bytes / current_size) * 90)
                quality = max(10, min(quality, 90))  # Keep quality between 10-90
                
                chunk_path = os.path.join(temp_dir, f"compressed_{Path(file_path).name}")
                
                # Convert to RGB if necessary (for JPEG saving)
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                img.save(chunk_path, format='JPEG', quality=quality, optimize=True)
                chunks.append(chunk_path)
                
        except Exception as e:
            print(f"Error processing image: {e}")
            return [file_path]  # Return original file if processing fails
        
        return chunks
    
    def needs_splitting(self, file_size, page_count):
        """Check if file needs to be split"""
        size_exceeds = file_size > self.max_size_bytes
        pages_exceed = page_count > self.max_pages
        return size_exceeds, pages_exceed
    
    def process_file_with_ocr(self, file_path, ocr_instance):
        """
        Process file by splitting if necessary and using OCR instance to extract text
        This method is called by DocumentOCR when file exceeds limits
        """
        if not os.path.exists(file_path):
            print(f"Error: File not found - {file_path}")
            return None
        
        print(f"FileProcessor: Processing {os.path.basename(file_path)}")
        
        # Get file information
        file_size, page_count = self.get_file_info(file_path)
        print(f"FileProcessor: File size: {file_size / (1024*1024):.2f} MB, Pages: {page_count}")
        
        # Check if splitting is needed
        size_exceeds, pages_exceed = self.needs_splitting(file_size, page_count)
        
        file_extension = Path(file_path).suffix.lower()
        chunks = [file_path]  # Default to original file
        
        if size_exceeds or pages_exceed:
            print("FileProcessor: File needs splitting...")
            
            if file_extension == '.pdf':
                if pages_exceed:
                    print(f"FileProcessor: Splitting by pages (max {self.max_pages} pages per chunk)")
                    chunks = self.split_pdf_by_pages(file_path, self.max_pages)
                elif size_exceeds:
                    print(f"FileProcessor: Splitting by size (max {self.max_size_mb} MB per chunk)")
                    chunks = self.split_pdf_by_size(file_path, self.max_size_bytes)
            else:
                # For images, only size splitting applies
                if size_exceeds:
                    print(f"FileProcessor: Compressing image to meet size limit ({self.max_size_mb} MB)")
                    chunks = self.split_image_by_size(file_path, self.max_size_bytes)
        
        print(f"FileProcessor: Processing {len(chunks)} chunk(s)...")
        
        # Process each chunk using the OCR instance and combine results
        all_text = []
        for i, chunk_path in enumerate(chunks):
            print(f"\nFileProcessor: Processing chunk {i+1}/{len(chunks)}: {os.path.basename(chunk_path)}")
            
            try:
                # Use the OCR instance to extract text from this chunk
                text = ocr_instance.extract_text_from_single_file(chunk_path)
                if text and text.strip():
                    all_text.append(text)
                    print(f"FileProcessor: ✓ Chunk {i+1} processed successfully ({len(text)} characters)")
                else:
                    print(f"FileProcessor: ⚠ Chunk {i+1} returned no text")
            except Exception as e:
                print(f"FileProcessor: ✗ Error processing chunk {i+1}: {e}")
        
        # Combine all extracted text seamlessly
        combined_text = '\n'.join(all_text)
        
        # Clean up temporary files
        for chunk_path in chunks:
            if chunk_path != file_path and os.path.exists(chunk_path):
                try:
                    os.remove(chunk_path)
                    # Also try to remove the temporary directory
                    temp_dir = os.path.dirname(chunk_path)
                    if temp_dir != os.path.dirname(file_path):
                        try:
                            os.rmdir(temp_dir)
                        except:
                            pass  # Directory might not be empty
                except Exception as e:
                    print(f"FileProcessor: Warning - Could not clean up temporary file {chunk_path}: {e}")
        
        print(f"FileProcessor: Combined {len(chunks)} chunks into {len(combined_text)} characters")
        return combined_text

    def process_file(self, file_path):
        """
        Legacy method - kept for backward compatibility
        Note: This method doesn't have access to OCR, so it can't extract text
        """
        print("FileProcessor: Warning - process_file() called without OCR instance")
        print("FileProcessor: Use process_file_with_ocr() instead for full functionality")
        return None