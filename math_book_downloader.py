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
    def __init__(self, progress_callback=None):
        self.download_dir = "math_books"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        self.downloaded_files = set()
        self.progress_callback = progress_callback
        
        # Define mathematical fields and their keywords
        self.math_fields = {
            'calculus': ['calculus', 'differential equations', 'integral', 'multivariable'],
            'algebra': ['algebra', 'linear algebra', 'abstract algebra', 'rings', 'groups'],
            'geometry': ['geometry', 'topology', 'differential geometry', 'algebraic geometry'],
            'analysis': ['analysis', 'real analysis', 'complex analysis', 'functional analysis'],
            'probability': ['probability', 'statistics', 'stochastic', 'random'],
            'number_theory': ['number theory', 'arithmetic', 'cryptography'],
            'discrete_math': ['discrete', 'combinatorics', 'graph theory', 'logic'],
            'applied_math': ['applied mathematics', 'numerical', 'optimization', 'modeling'],
            'other': []  # Default category for unclassified documents
        }
        
        # Create main download directory
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            
        # Create subdirectories for each field
        for field in self.math_fields.keys():
            field_dir = os.path.join(self.download_dir, field)
            if not os.path.exists(field_dir):
                os.makedirs(field_dir)

    def is_pdf_link(self, url):
        return url.lower().endswith('.pdf') or '.pdf' in url.lower()

    def sanitize_filename(self, filename):
        filename = unquote(filename)
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
        return filename[:200] if filename else 'unnamed.pdf'

    def determine_field(self, title, abstract=''):
        """Determine the mathematical field based on title and abstract."""
        # Convert inputs to lowercase for case-insensitive matching
        title_lower = title.lower()
        abstract_lower = abstract.lower() if abstract else ''
        
        # Check each field's keywords against the title and abstract
        for field, keywords in self.math_fields.items():
            for keyword in keywords:
                if keyword.lower() in title_lower or keyword.lower() in abstract_lower:
                    return field
        
        return 'other'  # Default category if no match is found

    def download_file(self, url, filename, source_dir=None, title='', abstract=''):
        if url in self.downloaded_files:
            return False

        try:
            logging.debug(f"Attempting to download: {url}")
            response = requests.get(url, headers=self.headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # Determine the mathematical field
            field = self.determine_field(title, abstract)
            
            # Create the full path: math_books/field/source_dir/
            if source_dir:
                target_dir = os.path.join(self.download_dir, field, source_dir)
            else:
                target_dir = os.path.join(self.download_dir, field)
                
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            
            filepath = os.path.join(target_dir, filename)
            total_size = int(response.headers.get('content-length', 0))
            
            if total_size > 0:
                logging.info(f"File size: {total_size/1024/1024:.2f} MB")

            block_size = 8192
            downloaded_size = 0

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        downloaded_size += len(chunk)
                        f.write(chunk)
                        
                        # Calculate and report progress
                        if total_size > 0 and self.progress_callback:
                            progress = (downloaded_size / total_size) * 100
                            self.progress_callback(filename, progress)

            if os.path.getsize(filepath) > 0:
                self.downloaded_files.add(url)
                logging.info(f"Successfully downloaded: {filename} to {field}/{source_dir if source_dir else ''}")
                # Signal completion
                if self.progress_callback:
                    self.progress_callback(filename, 100)
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
                            title_text = title.text.strip()
                            abstract = summary.text.strip()
                            
                            if ('textbook' in abstract.lower() or 'lecture notes' in abstract.lower() or 
                                'course notes' in abstract.lower() or 'introduction to' in abstract.lower()):
                                
                                pdf_link = entry.find('link', {'title': 'pdf'})
                                if pdf_link and 'href' in pdf_link.attrs:
                                    pdf_url = pdf_link['href']
                                    if not pdf_url.endswith('.pdf'):
                                        pdf_url = pdf_url.replace('/abs/', '/pdf/') + '.pdf'
                                    
                                    filename = self.sanitize_filename(f"{category}_{title_text}.pdf")
                                    self.download_file(pdf_url, filename, "arxiv", title_text, abstract)
                                    time.sleep(3)
                    except Exception as e:
                        logging.error(f"Error processing arXiv paper: {str(e)}")
                        continue

                time.sleep(5)
            except Exception as e:
                logging.error(f"Error scraping arXiv for {category}: {str(e)}")

    def scrape_open_textbook_library(self):
        """Scrape Open Textbook Library for mathematics books."""
        base_url = "https://open.umn.edu/opentextbooks/"
        search_terms = [
            "mathematics",
            "calculus",
            "algebra",
            "statistics",
            "geometry"
        ]
        
        for term in search_terms:
            try:
                url = f"{base_url}textbooks/?searchText={term}"
                logging.info(f"Searching Open Textbook Library for: {term}")
                
                response = requests.get(url, headers=self.headers, timeout=30)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all book entries in the search results
                book_entries = soup.find_all('div', class_='book-index-item')
                logging.info(f"Found {len(book_entries)} potential books for term: {term}")
                
                for book_entry in book_entries:
                    try:
                        # Get the book's detail page URL and title
                        title_link = book_entry.find('a', class_='book-index-item__title')
                        if not title_link:
                            continue
                            
                        title = title_link.text.strip()
                        book_url = urljoin(base_url, title_link['href'])
                        
                        logging.info(f"Processing book: {title}")
                        logging.info(f"Book URL: {book_url}")
                        
                        # Get the book's detail page
                        book_response = requests.get(book_url, headers=self.headers, timeout=30)
                        book_soup = BeautifulSoup(book_response.text, 'html.parser')
                        
                        # Try different methods to find download links
                        download_links = []
                        
                        # Method 1: Check the download button section
                        download_section = book_soup.find('div', class_='book-download')
                        if download_section:
                            download_links.extend(download_section.find_all('a', href=True))
                        
                        # Method 2: Check for any links containing "download" or "pdf"
                        download_links.extend(book_soup.find_all('a', 
                            href=lambda x: x and any(word in x.lower() for word in ['download', '.pdf', 'get-book'])))
                        
                        # Method 3: Check specific button classes
                        download_links.extend(book_soup.find_all('a', class_=['button', 'btn', 'download-button']))
                        
                        for link in download_links:
                            try:
                                href = link['href']
                                # Skip non-PDF links and internal anchors
                                if not href or href.startswith('#'):
                                    continue
                                    
                                pdf_url = href if href.startswith('http') else urljoin(book_url, href)
                                
                                # Follow redirects to get the final URL if needed
                                try:
                                    head_response = requests.head(pdf_url, headers=self.headers, allow_redirects=True, timeout=10)
                                    final_url = head_response.url
                                    content_type = head_response.headers.get('content-type', '').lower()
                                    
                                    if 'pdf' in content_type or final_url.lower().endswith('.pdf'):
                                        logging.info(f"Found valid PDF link: {final_url}")
                                        filename = self.sanitize_filename(f"opentextbook_{title}.pdf")
                                        
                                        if self.download_file(final_url, filename, "open_textbook", title):
                                            break  # Successfully downloaded one version
                                except requests.exceptions.RequestException as e:
                                    logging.error(f"Error checking PDF URL {pdf_url}: {str(e)}")
                                    continue
                                
                            except Exception as e:
                                logging.error(f"Error processing download link: {str(e)}")
                                continue
                        
                        time.sleep(3)
                    except Exception as e:
                        logging.error(f"Error processing Open Textbook: {str(e)}")
                        continue
                
                time.sleep(5)
            except Exception as e:
                logging.error(f"Error searching Open Textbook Library for {term}: {str(e)}")
                continue

    def scrape_oer_commons(self):
        """Scrape OER Commons for mathematics materials."""
        base_url = "https://www.oercommons.org/curated-collections"
        subjects = [
            "mathematics",
            "algebra",
            "geometry",
            "calculus",
            "statistics"
        ]
        
        for subject in subjects:
            try:
                params = {
                    'batch_start': 0,
                    'batch_size': 50,
                    'sort_by': 'rating',
                    'view_mode': 'summary',
                    'f.search': subject,
                    'f.sublevel': ['community-college', 'college-upper-division', 'graduate-professional'],
                    'f.material_types': ['textbook', 'full-course'],
                    'f.general_subject': 'mathematics'
                }
                
                logging.info(f"Searching OER Commons for: {subject}")
                response = requests.get(base_url, params=params, headers=self.headers, timeout=30)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all resource items
                resources = soup.find_all(['div', 'article'], class_=['resource-item', 'resource-summary'])
                logging.info(f"Found {len(resources)} potential resources for: {subject}")
                
                for resource in resources:
                    try:
                        # Get title and link
                        title_elem = resource.find(['h2', 'h3', 'a'], class_=['item-title', 'resource-title'])
                        link_elem = resource.find('a', href=lambda x: x and '/courses/' in x or '/resources/' in x)
                        
                        if not (title_elem and link_elem):
                            continue
                            
                        title = title_elem.text.strip()
                        resource_url = urljoin(base_url, link_elem['href'])
                        
                        logging.info(f"Processing resource: {title}")
                        logging.info(f"Resource URL: {resource_url}")
                        
                        # Get resource detail page
                        resource_response = requests.get(resource_url, headers=self.headers, timeout=30)
                        resource_soup = BeautifulSoup(resource_response.text, 'html.parser')
                        
                        # Look for download links in multiple locations
                        download_links = []
                        
                        # Method 1: Direct download buttons
                        download_links.extend(resource_soup.find_all('a', class_=['download-button', 'download-link', 'resource-download']))
                        
                        # Method 2: Resource links section
                        resource_links = resource_soup.find(['div', 'section'], class_=['resource-links', 'download-section'])
                        if resource_links:
                            download_links.extend(resource_links.find_all('a', href=True))
                        
                        # Method 3: Check metadata for URLs
                        meta_links = resource_soup.find_all('meta', property=['og:url', 'citation_pdf_url'])
                        for meta in meta_links:
                            if 'content' in meta.attrs:
                                download_links.append({'href': meta['content']})
                        
                        # Method 4: Look for embedded content
                        embed_frames = resource_soup.find_all(['iframe', 'embed'], src=True)
                        for frame in embed_frames:
                            if '.pdf' in frame['src'].lower():
                                download_links.append({'href': frame['src']})
                        
                        for link in download_links:
                            try:
                                href = link.get('href')
                                if not href or href.startswith('#'):
                                    continue
                                
                                pdf_url = href if href.startswith('http') else urljoin(resource_url, href)
                                
                                # Check if it's a valid PDF URL
                                try:
                                    head_response = requests.head(pdf_url, headers=self.headers, allow_redirects=True, timeout=10)
                                    final_url = head_response.url
                                    content_type = head_response.headers.get('content-type', '').lower()
                                    
                                    if 'pdf' in content_type or final_url.lower().endswith('.pdf'):
                                        logging.info(f"Found valid PDF link: {final_url}")
                                        filename = self.sanitize_filename(f"oer_{title}.pdf")
                                        
                                        if self.download_file(final_url, filename, "oer_commons", title):
                                            break  # Successfully downloaded one version
                                except requests.exceptions.RequestException as e:
                                    logging.error(f"Error checking PDF URL {pdf_url}: {str(e)}")
                                    continue
                                
                            except Exception as e:
                                logging.error(f"Error processing download link: {str(e)}")
                                continue
                        
                        time.sleep(3)
                    except Exception as e:
                        logging.error(f"Error processing OER resource: {str(e)}")
                        continue
                
                time.sleep(5)
            except Exception as e:
                logging.error(f"Error searching OER Commons for {subject}: {str(e)}")
                continue

    def scrape_merlot(self):
        """Scrape MERLOT for mathematics materials."""
        base_url = "https://www.merlot.org/merlot/materials.htm"
        categories = [
            "Mathematics",
            "Statistics",
            "Calculus",
            "Linear Algebra",
            "Abstract Algebra"
        ]
        
        for category in categories:
            try:
                params = {
                    'keywords': category,
                    'materialType': 'Open Textbook',
                    'sort.property': 'relevance'
                }
                
                logging.info(f"Searching MERLOT for: {category}")
                response = requests.get(base_url, params=params, headers=self.headers, timeout=30)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for material in soup.find_all('div', class_='material-item'):
                    try:
                        title = material.find('h3', class_='title')
                        link = material.find('a', class_='material-link')
                        
                        if title and link:
                            material_url = urljoin(base_url, link['href'])
                            material_response = requests.get(material_url, headers=self.headers, timeout=30)
                            material_soup = BeautifulSoup(material_response.text, 'html.parser')
                            
                            download_link = material_soup.find('a', href=lambda x: x and x.endswith('.pdf'))
                            if download_link:
                                pdf_url = download_link['href']
                                if not pdf_url.startswith('http'):
                                    pdf_url = urljoin(base_url, pdf_url)
                                
                                filename = self.sanitize_filename(f"merlot_{title.text}.pdf")
                                self.download_file(pdf_url, filename, "merlot", title.text)
                                time.sleep(3)
                    except Exception as e:
                        logging.error(f"Error processing MERLOT resource: {str(e)}")
                        continue
                
                time.sleep(5)
            except Exception as e:
                logging.error(f"Error searching MERLOT for {category}: {str(e)}")

    def run(self, selected_sources=None):
        """Run the downloader with selected sources."""
        logging.info("Starting mathematics document downloader...")
        logging.info("Documents will be organized in the following directories:")
        for field in self.math_fields.keys():
            logging.info(f"- {field}/")
        
        source_methods = {
            'arxiv': self.scrape_arxiv,
            'open_textbook': self.scrape_open_textbook_library,
            'oer_commons': self.scrape_oer_commons,
            'merlot': self.scrape_merlot
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
            logging.info(f"Files are organized by field in the '{self.download_dir}' directory.")

if __name__ == "__main__":
    downloader = MathBookDownloader()
    downloader.run() 