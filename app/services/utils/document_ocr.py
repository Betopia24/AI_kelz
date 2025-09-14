import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from google.cloud import documentai
from google.api_core.client_options import ClientOptions

# Import the file converter and processor
from app.services.utils.convert_file import FileConverter
from app.services.utils.process_file import FileProcessor

# Load environment variables
load_dotenv()

class DocumentOCR:

    def process_file(self, file_path):
        """
        Legacy compatibility: delegate to FileProcessor.process_file.
        Note: This does not perform OCR, just file splitting/processing as in the legacy method.
        """
        return self.file_processor.process_file(file_path)
    def __init__(self):
        """Initialize Document OCR with all required components"""
        # Google Document AI configuration
        self.project_id = os.getenv('PROJECT_ID')
        self.location = os.getenv('LOCATION') 
        self.processor_id = os.getenv('PROCESSOR_ID')
        self.processor_version = os.getenv('PROCESSOR_VERSION')
        
        # Initialize file converter and processor
        self.file_converter = FileConverter()
        self.file_processor = FileProcessor()
        
        # Set size and page limits
        self.max_size_mb = 10
        self.max_pages = 10
        self.max_size_bytes = self.max_size_mb * 1024 * 1024
        
        # Set credentials
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        
        # Supported formats summary
        self.pdf_image_formats = ['.pdf', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.tiff', '.tif']
        self.convertible_formats = list(self.file_converter.supported_formats.keys())

    def get_mime_type(self, file_path):
        """Get MIME type from file extension"""
        mime_types = {
            '.pdf': 'application/pdf',
            '.png': 'image/png', 
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff'
        }
        extension = Path(file_path).suffix.lower()
        return mime_types.get(extension, 'application/octet-stream')
    
    def is_pdf_or_image(self, file_path):
        """Check if file is PDF or image format (directly supported by Document AI)"""
        extension = Path(file_path).suffix.lower()
        return extension in self.pdf_image_formats
    
    def get_page_count(self, file_path):
        """Get the number of pages in a PDF file"""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            page_count = doc.page_count
            doc.close()
            return page_count
        except Exception:
            # Fallback for non-PDF files or if PyMuPDF is not available
            return 1

    def check_file_limits(self, file_path):
        """Check if file exceeds size or page limits"""
        file_size = os.path.getsize(file_path)
        page_count = self.get_page_count(file_path)
        
        size_exceeds = file_size > self.max_size_bytes
        pages_exceed = page_count > self.max_pages
        
        return size_exceeds, pages_exceed, file_size, page_count

    def prepare_file_for_ocr(self, file_path):
        """
        Step 1: Prepare file for OCR processing.
        If file is not PDF/image, convert it to PDF using convert_file.py
        Returns: (file_path_to_process, is_temporary_file)
        """
        extension = Path(file_path).suffix.lower()
        
        # Check if file is directly supported (PDF or image)
        if self.is_pdf_or_image(file_path):
            return file_path, False
        
        # Check if file can be converted using FileConverter
        if not self.file_converter.is_convertible(file_path):
            supported_formats = self.pdf_image_formats + self.convertible_formats
            raise ValueError(f"Unsupported file format: {extension}. Supported formats: {', '.join(set(supported_formats))}")
        
        # Convert file to PDF using convert_file.py
        try:
            # Create temporary PDF file path
            temp_pdf_path = os.path.join(
                tempfile.gettempdir(), 
                f"{Path(file_path).stem}_converted_for_ocr.pdf"
            )
            
            # Use FileConverter to convert the file
            converted_pdf = self.file_converter.convert_to_pdf(file_path, temp_pdf_path)
            
            # Verify the conversion was successful
            if not os.path.exists(converted_pdf):
                raise Exception(f"Conversion failed - PDF file not created: {converted_pdf}")
                
            if not converted_pdf.lower().endswith('.pdf'):
                raise Exception(f"Conversion did not produce a PDF file: {converted_pdf}")
            
            return converted_pdf, True
            
        except Exception as e:
            raise Exception(f"Failed to convert {extension} file to PDF: {e}")

    def extract_text_from_single_file(self, file_path):
        """Extract text from a single PDF or image file using Google Document AI"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            # Verify file is in supported format
            mime_type = self.get_mime_type(file_path)
            supported_mime_types = [
                'application/pdf', 'image/png', 'image/jpeg',
                'image/gif', 'image/webp', 'image/bmp', 'image/tiff'
            ]
            
            if mime_type not in supported_mime_types:
                raise ValueError(f"Unsupported MIME type for OCR: {mime_type}")
            
            # Create Document AI client
            client = documentai.DocumentProcessorServiceClient(
                client_options=ClientOptions(
                    api_endpoint=f"{self.location}-documentai.googleapis.com"
                )
            )
            
            # Get processor name
            name = client.processor_version_path(
                self.project_id, self.location, self.processor_id, self.processor_version
            )
            
            # Read file content
            with open(file_path, "rb") as f:
                file_content = f.read()
            
            # Create Document AI request
            raw_document = documentai.RawDocument(
                content=file_content, 
                mime_type=mime_type
            )
            
            request = documentai.ProcessRequest(
                name=name,
                raw_document=raw_document
            )
            
            # Process document
            result = client.process_document(request=request)
            document = result.document
            
            # Extract text
            extracted_text = document.text if hasattr(document, 'text') else ''
            
            return extracted_text if extracted_text.strip() else ''
            
        except Exception as e:
            raise e

    def extract_text(self, file_path):
        """
        Main text extraction method following the complete workflow:
        1. Check file type - if not PDF/image, convert to PDF using convert_file.py
        2. Check size and pages - if exceeds limits, send to process_file.py
        3. Extract text and return combined result
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        processed_file_path = None
        is_temporary = False
        
        try:
            # STEP 1: Prepare file for OCR (convert if necessary)
            processed_file_path, is_temporary = self.prepare_file_for_ocr(file_path)
            
            # STEP 2: Check file limits
            size_exceeds, pages_exceed, file_size, page_count = self.check_file_limits(processed_file_path)
            
            # STEP 3: Process based on limits
            if size_exceeds or pages_exceed:
                # Use process_file.py to handle large files
                extracted_text = self.file_processor.process_file_with_ocr(processed_file_path, self)
                
                if not extracted_text:
                    return "Error: Failed to process large file"
                    
            else:
                # Process directly with Document AI
                extracted_text = self.extract_text_from_single_file(processed_file_path)
            
            return extracted_text if extracted_text else "Error: No text could be extracted"
            
        except Exception as e:
            return f"Error: {str(e)}"
            
        finally:
            # CLEANUP: Remove temporary files
            if is_temporary and processed_file_path and os.path.exists(processed_file_path):
                try:
                    os.remove(processed_file_path)
                except Exception:
                    pass  # Silent cleanup

    def extract_text_from_files(self, file_paths):
        """
        Extract text from multiple files.
        Args:
            file_paths (list): List of file paths to process
        Returns:
            dict: {filename: extracted_text}
        """
        results = {}
        for file_path in file_paths:
            try:
                text = self.extract_text(file_path)
                results[os.path.basename(file_path)] = text
            except Exception as e:
                results[os.path.basename(file_path)] = f"Error: {str(e)}"
        
        return results

    def get_supported_formats(self):
        """Get comprehensive list of all supported file formats"""
        all_supported = list(set(self.pdf_image_formats + self.convertible_formats))
        
        return {
            'directly_supported_for_ocr': self.pdf_image_formats,
            'convertible_formats': self.convertible_formats,
            'all_supported_formats': sorted(all_supported),
            'total_supported': len(all_supported)
        }

    def validate_file(self, file_path):
        """Validate if a file can be processed"""
        if not os.path.exists(file_path):
            return False, f"File does not exist: {file_path}"
        
        extension = Path(file_path).suffix.lower()
        
        if self.is_pdf_or_image(file_path):
            return True, f"File is directly supported for OCR ({extension})"
        elif self.file_converter.is_convertible(file_path):
            return True, f"File can be converted to PDF ({extension})"
        else:
            supported = self.get_supported_formats()['all_supported_formats']
            return False, f"Unsupported format: {extension}. Supported: {', '.join(supported)}"

    def process_single_file(self, file_path):
        """Process a single file and return the extracted text"""
        # Validate file first
        is_valid, message = self.validate_file(file_path)
        if not is_valid:
            return None
        
        # Process the file
        try:
            text = self.extract_text(file_path)
            
            if text and not text.startswith("Error:"):
                return text
            else:
                return None
                
        except Exception as e:
            return None

# Example usage and testing functions
def test_single_file(file_path):
    """Test processing a single file"""
    ocr = DocumentOCR()
    result = ocr.process_single_file(file_path)
    return result

def test_multiple_files(file_paths):
    """Test processing multiple files"""
    ocr = DocumentOCR()
    results = ocr.extract_text_from_files(file_paths)
    return results

def show_supported_formats():
    """Display all supported file formats"""
    ocr = DocumentOCR()
    formats = ocr.get_supported_formats()
    return formats

