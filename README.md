# Mathematics Document Downloader

A Python GUI application for downloading mathematics-related documents from various sources.

## Features

- Downloads from multiple sources:
  - arXiv (research papers, lecture notes)
  - MIT OpenCourseWare (course materials)
  - Project Gutenberg (classic mathematics books)
- User-friendly GUI interface
- Organized downloads by source and category
- Progress tracking and logging
- Configurable download directory

## Requirements

- Python 3.x
- PySide6
- BeautifulSoup4
- Requests

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mathematics-downloader
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the GUI application:
```bash
python math_downloader_gui.py
```

2. Select your desired sources:
   - arXiv: Research papers and lecture notes
   - MIT OCW: Course materials and problem sets
   - Project Gutenberg: Classic mathematics books

3. Choose a download directory (optional)

4. Click "Start Download" to begin

5. Monitor progress in the log display

## File Organization

Downloads are organized in the following structure:
```
math_books/
├── arxiv/
│   └── [Category]_[Title].pdf
├── mit_ocw/
│   └── mit_[Title].pdf
└── gutenberg/
    └── gutenberg_[Title].pdf
```

## Contributing

Feel free to open issues or submit pull requests for improvements.

## License

This project is open source and available under the MIT License. 