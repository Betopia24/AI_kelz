
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from google.cloud import documentai
from google.api_core.client_options import ClientOptions

# Import the file converter and processor

from app.services.utils.convert_file import FileConverter
from  app.services.utils.process_file import FileProcessor  
# Load environment variables
load_dotenv()

class DocumentOCR:
    def __init__(self):
        """Initialize with environment variables"""
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
        supported_extensions = ['.pdf', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.tiff', '.tif']
        return extension in supported_extensions
    
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
        Prepare file for OCR processing.
        Step 1: If file is not PDF/image, convert it to PDF first.
        Returns: (file_path_to_process, is_temporary_file)
        """
        extension = Path(file_path).suffix.lower()
        print(f"File extension: {extension}")
        
        if self.is_pdf_or_image(file_path):
            # File is already in supported format
            print(f"File {os.path.basename(file_path)} is in supported format ({extension})")
            return file_path, False
        
        print(f"File {os.path.basename(file_path)} is not PDF/image, checking if convertible...")
        
        # Check if file can be converted
        if not self.file_converter.is_convertible(file_path):
            extension = Path(file_path).suffix.lower()
            raise ValueError(f"File format {extension} is not supported for conversion or OCR processing")
        
        # Convert file to PDF
        print(f"Converting {os.path.basename(file_path)} ({extension}) to PDF...")
        try:
            # Create temporary PDF file
            temp_pdf_path = os.path.join(
                tempfile.gettempdir(), 
                f"{Path(file_path).stem}_converted.pdf"
            )
            
            print(f"Conversion target: {temp_pdf_path}")
            converted_pdf = self.file_converter.convert_to_pdf(file_path, temp_pdf_path)
            print(f"Successfully converted to PDF: {os.path.basename(converted_pdf)}")
            
            # Verify the converted file exists and is a PDF
            if not os.path.exists(converted_pdf):
                raise Exception(f"Converted PDF file not found: {converted_pdf}")
                
            if not converted_pdf.lower().endswith('.pdf'):
                raise Exception(f"Conversion did not produce a PDF file: {converted_pdf}")
            
            return converted_pdf, True
            
        except Exception as e:
            print(f"Conversion error details: {str(e)}")
            raise Exception(f"Failed to convert file to PDF: {e}")

    def extract_text_from_single_file(self, file_path):
        """Extract text from a single file using Google Document AI"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            # Get MIME type of the file
            mime_type = self.get_mime_type(file_path)
            supported_mime_types = [
                'application/pdf', 'image/png', 'image/jpeg', 'image/jpg',
                'image/gif', 'image/webp', 'image/bmp', 'image/tiff'
            ]
            if mime_type not in supported_mime_types:
                raise ValueError(f"Unsupported file type after conversion: {mime_type}. Supported types: {', '.join(supported_mime_types)}")
            
            # Create client
            client = documentai.DocumentProcessorServiceClient(
                client_options=ClientOptions(
                    api_endpoint=f"{self.location}-documentai.googleapis.com"
                )
            )
            
            # Get processor name
            name = client.processor_version_path(
                self.project_id, self.location, self.processor_id, self.processor_version
            )
            
            # Read file
            with open(file_path, "rb") as f:
                file_content = f.read()
            
            # Create request
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
            
            if not hasattr(document, 'text') or not document.text.strip():
                print("[WARNING] No text extracted from the document.")
            
            return document.text if hasattr(document, 'text') else ''
            
        except Exception as e:
            print(f"Error extracting text: {e}")
            raise e

    def extract_text(self, file_path):
        """
        Main text extraction method following the exact workflow:
        1. Check file type - if not PDF/image, convert to PDF
        2. Check size and pages - if exceeds limits, send to processor
        3. Extract text and return combined result
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        print(f"Processing: {os.path.basename(file_path)}")
        
        # Step 1: Prepare file (convert if necessary)
        try:
            processed_file_path, is_temporary = self.prepare_file_for_ocr(file_path)
        except Exception as e:
            # Improved error handling for conversion failures
            return f"Error: Could not prepare file for OCR. Details: {str(e)}"
        
        try:
            # Step 2: Check file limits
            size_exceeds, pages_exceed, file_size, page_count = self.check_file_limits(processed_file_path)
            
            print(f"File size: {file_size / (1024*1024):.2f} MB")
            print(f"Page count: {page_count}")
            
            # Step 3: Process based on limits
            if size_exceeds or pages_exceed:
                print(f"File exceeds limits (Size: {size_exceeds}, Pages: {pages_exceed})")
                print("Sending to file processor for splitting...")
                try:
                    # Use FileProcessor to handle large files
                    combined_text = self.file_processor.process_file_with_ocr(processed_file_path, self)
                    return combined_text
                except Exception as e:
                    return f"Error: Could not process large file. Details: {str(e)}"
            else:
                print("File within limits, processing directly...")
                # Process directly
                try:
                    return self.extract_text_from_single_file(processed_file_path)
                except Exception as e:
                    return f"Error: Could not extract text from file. Details: {str(e)}"
        finally:
            # Clean up temporary file if created
            if 'is_temporary' in locals() and is_temporary and os.path.exists(processed_file_path):
                try:
                    os.remove(processed_file_path)
                    print(f"Cleaned up temporary file: {os.path.basename(processed_file_path)}")
                except Exception as e:
                    print(f"Warning: Could not remove temporary file {processed_file_path}: {e}")

    def process_file(self, file_path):
        """Process file and return extracted text"""
        try:
            print(f"Starting to process: {os.path.basename(file_path)}")
            
            # Show file type information
            if self.is_pdf_or_image(file_path):
                print(f"File type: Directly supported ({self.get_mime_type(file_path)})")
            elif self.file_converter.is_convertible(file_path):
                extension = Path(file_path).suffix.lower()
                print(f"File type: Will be converted from {extension} to PDF")
            else:
                extension = Path(file_path).suffix.lower()
                print(f"File type: Unsupported ({extension})")
                return None
            
            text = self.extract_text(file_path)
            
            print(f"\n=== EXTRACTION COMPLETE ===")
            print(f"Total characters extracted: {len(text)}")
            print(f"=== EXTRACTED TEXT ===")
            print(text)
            
            return text
        except Exception as e:
            print(f"Error: {e}")
            return None

    def test_file_processing_workflow(self, file_path):
        """
        Test function to debug the file processing workflow
        """
        print(f"\n=== TESTING FILE PROCESSING WORKFLOW ===")
        print(f"File: {file_path}")
        print(f"File exists: {os.path.exists(file_path)}")
        
        if not os.path.exists(file_path):
            print("ERROR: File does not exist!")
            return False
            
        extension = Path(file_path).suffix.lower()
        print(f"Extension: {extension}")
        
        # Test step 1: Check if PDF or image
        is_supported = self.is_pdf_or_image(file_path)
        print(f"Is PDF or Image: {is_supported}")
        
        # Test step 2: Check if convertible
        is_convertible = self.file_converter.is_convertible(file_path)
        print(f"Is convertible: {is_convertible}")
        
        if not is_supported and not is_convertible:
            print("ERROR: File is neither directly supported nor convertible!")
            return False
            
        print("File processing workflow test: PASSED")
        return True

    def get_supported_formats(self):
        """Get list of all supported file formats"""
        directly_supported = ['.pdf', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.tiff', '.tif']
        convertible_formats = list(self.file_converter.supported_formats.keys())
        
        all_supported = directly_supported + convertible_formats
        return {
            'directly_supported': directly_supported,
            'convertible_formats': convertible_formats,
            'all_supported': sorted(list(set(all_supported)))
        }