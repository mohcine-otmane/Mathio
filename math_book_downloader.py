import os
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin, quote, unquote
import logging
import re
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings

# Suppress XMLParsedAsHTMLWarning warnings
warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)

# Set up logging with more detailed information
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('math_book_downloader.log'),
        logging.StreamHandler()
    ]
)

class MathBookDownloader:
    def __init__(self):
        self.download_dir = "math_books"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        self.downloaded_files = set()
        
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

    def is_pdf_link(self, url):
        return url.lower().endswith('.pdf') or '.pdf' in url.lower()

    def sanitize_filename(self, filename):
        filename = unquote(filename)
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
        return filename[:200] if filename else 'unnamed.pdf'

    def download_file(self, url, filename, source_dir=None):
        if url in self.downloaded_files:
            return False

        try:
            logging.debug(f"Attempting to download: {url}")
            response = requests.get(url, headers=self.headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # Create source-specific subdirectory if specified
            if source_dir:
                target_dir = os.path.join(self.download_dir, source_dir)
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
            else:
                target_dir = self.download_dir
            
            filepath = os.path.join(target_dir, filename)
            total_size = int(response.headers.get('content-length', 0))
            
            if total_size > 0:
                logging.info(f"File size: {total_size/1024/1024:.2f} MB")

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            if os.path.getsize(filepath) > 0:
                self.downloaded_files.add(url)
                logging.info(f"Successfully downloaded: {filename}")
                return True
            else:
                os.remove(filepath)
                logging.error(f"Downloaded file was empty: {filename}")
                return False

        except Exception as e:
            logging.error(f"Error downloading {url}: {str(e)}")
            return False

    def scrape_arxiv(self):
        """Scrape arXiv for mathematics papers and books."""
        categories = {
            "math.AG": "Algebraic Geometry",
            "math.AT": "Algebraic Topology",
            "math.RA": "Rings and Algebras",
            "math.GT": "Geometric Topology",
            "math.NT": "Number Theory",
            "math.FA": "Functional Analysis",
            "math.CA": "Classical Analysis",
            "math.OA": "Operator Algebras",
            "math.RT": "Representation Theory",
            "math.QA": "Quantum Algebra",
            "math.DG": "Differential Geometry",
            "math.AP": "Analysis of PDEs",
            "math.PR": "Probability Theory",
            "math.ST": "Statistics Theory",
            "math.LO": "Logic"
        }

        for category, description in categories.items():
            try:
                url = f"http://export.arxiv.org/api/query?search_query=cat:{category}+AND+%28%22textbook%22+OR+%22lecture+notes%22%29&start=0&max_results=50&sortBy=relevance"
                logging.info(f"Searching arXiv for: {description}")
                
                response = requests.get(url, headers=self.headers, timeout=30)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                for entry in soup.find_all('entry'):
                    try:
                        title = entry.find('title')
                        summary = entry.find('summary')
                        
                        if title and summary:
                            title = title.text.strip()
                            abstract = summary.text.strip().lower()
                            
                            if ('textbook' in abstract or 'lecture notes' in abstract or 
                                'course notes' in abstract or 'introduction to' in abstract):
                                
                                pdf_link = entry.find('link', {'title': 'pdf'})
                                if pdf_link and 'href' in pdf_link.attrs:
                                    pdf_url = pdf_link['href']
                                    if not pdf_url.endswith('.pdf'):
                                        pdf_url = pdf_url.replace('/abs/', '/pdf/') + '.pdf'
                                    
                                    filename = self.sanitize_filename(f"{category}_{title}.pdf")
                                    self.download_file(pdf_url, filename, "arxiv")
                                    time.sleep(3)
                    except Exception as e:
                        logging.error(f"Error processing arXiv paper: {str(e)}")
                        continue

                time.sleep(5)
            except Exception as e:
                logging.error(f"Error scraping arXiv for {category}: {str(e)}")

    def scrape_mit_ocw(self):
        """Scrape MIT OpenCourseWare for mathematics materials."""
        base_url = "https://ocw.mit.edu"
        math_departments = [
            "/courses/mathematics/",
            "/courses/electrical-engineering-and-computer-science/"
        ]
        
        for dept_path in math_departments:
            try:
                url = base_url + dept_path
                logging.info(f"Searching MIT OCW: {dept_path}")
                
                response = requests.get(url, headers=self.headers, timeout=30)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for course_link in soup.find_all('a', href=True):
                    if '/courses/' in course_link['href'] and any(term in course_link.text.lower() 
                        for term in ['calculus', 'algebra', 'analysis', 'topology', 'geometry']):
                        try:
                            course_url = urljoin(base_url, course_link['href'])
                            course_response = requests.get(course_url, headers=self.headers, timeout=30)
                            course_soup = BeautifulSoup(course_response.text, 'html.parser')
                            
                            for pdf_link in course_soup.find_all('a', href=True):
                                if pdf_link['href'].lower().endswith('.pdf'):
                                    pdf_url = urljoin(base_url, pdf_link['href'])
                                    filename = self.sanitize_filename(f"mit_{pdf_link.text}.pdf")
                                    self.download_file(pdf_url, filename, "mit_ocw")
                                    time.sleep(2)
                            
                            time.sleep(3)
                        except Exception as e:
                            logging.error(f"Error processing MIT OCW course: {str(e)}")
                            continue
                
                time.sleep(5)
            except Exception as e:
                logging.error(f"Error scraping MIT OCW: {str(e)}")

    def scrape_project_gutenberg(self):
        """Scrape Project Gutenberg for mathematics books."""
        search_terms = [
            "mathematics textbook",
            "geometry textbook",
            "algebra textbook",
            "calculus textbook"
        ]
        
        base_url = "https://www.gutenberg.org/ebooks/search/?query="
        
        for term in search_terms:
            try:
                url = base_url + quote(term)
                logging.info(f"Searching Project Gutenberg for: {term}")
                
                response = requests.get(url, headers=self.headers, timeout=30)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for book_link in soup.select('.booklink'):
                    try:
                        title = book_link.select_one('.title')
                        if title:
                            book_url = urljoin(base_url, book_link.find('a')['href'])
                            book_response = requests.get(book_url, headers=self.headers, timeout=30)
                            book_soup = BeautifulSoup(book_response.text, 'html.parser')
                            
                            for download_link in book_soup.find_all('a', href=True):
                                if download_link['href'].endswith('.pdf'):
                                    pdf_url = urljoin(base_url, download_link['href'])
                                    filename = self.sanitize_filename(f"gutenberg_{title.text}.pdf")
                                    if self.download_file(pdf_url, filename, "gutenberg"):
                                        break
                            
                            time.sleep(2)
                    except Exception as e:
                        logging.error(f"Error processing Gutenberg book: {str(e)}")
                        continue
                
                time.sleep(5)
            except Exception as e:
                logging.error(f"Error searching Project Gutenberg for {term}: {str(e)}")

    def run(self, selected_sources=None):
        """Run the downloader with selected sources."""
        logging.info("Starting mathematics document downloader...")
        
        source_methods = {
            'arxiv': self.scrape_arxiv,
            'mit_ocw': self.scrape_mit_ocw,
            'gutenberg': self.scrape_project_gutenberg
        }
        
        if selected_sources is None:
            selected_sources = list(source_methods.keys())
        
        for source in selected_sources:
            if source in source_methods:
                try:
                    source_methods[source]()
                except Exception as e:
                    logging.error(f"Error processing source {source}: {str(e)}")
        
        if len(self.downloaded_files) == 0:
            logging.warning("No files were downloaded. This might be due to:")
            logging.warning("1. Network connectivity issues")
            logging.warning("2. No matching documents found")
            logging.warning("3. Rate limiting from the servers")
            logging.warning("Please check the log file for detailed error messages.")
        else:
            logging.info(f"Download process completed! Downloaded {len(self.downloaded_files)} files.")
            logging.info(f"Files are saved in the '{self.download_dir}' directory.")

if __name__ == "__main__":
    downloader = MathBookDownloader()
    downloader.run() 