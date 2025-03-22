# Mathematics Document Downloader

A Python-based GUI application for downloading mathematics educational resources, textbooks, and academic materials from various sources. This tool helps students, educators, and researchers easily access mathematical content from arXiv, MIT OpenCourseWare, and Project Gutenberg.

## 🎯 Key Features

- 📚 Multi-source document collection:
  - **arXiv**: Research papers, lecture notes, and academic materials
  - **MIT OpenCourseWare**: Course materials, problem sets, and educational resources
  - **Project Gutenberg**: Classic mathematics books and historical texts
- 🖥️ Modern, user-friendly GUI built with PySide6
- 📂 Smart organization of downloads by source and category
- 📊 Real-time progress tracking and detailed logging
- 🎛️ Configurable download directory and source selection
- 🔍 Intelligent filtering for educational content

## 🛠️ Requirements

- Python 3.x
- PySide6 (Qt for Python)
- BeautifulSoup4 (for parsing)
- Requests (for downloads)

## 📥 Installation

1. Clone the repository:
```bash
git clone https://github.com/mohcine-otmane/Mathio.git
cd Mathio
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## 🚀 Usage

1. Launch the GUI application:
```bash
python math_downloader_gui.py
```

2. Select your desired sources:
   - **arXiv**: For research papers and academic lecture notes
   - **MIT OCW**: For university-level course materials
   - **Project Gutenberg**: For classic mathematics textbooks

3. Choose a download directory (optional)

4. Click "Start Download" to begin

5. Monitor progress in the log display

## 📁 File Organization

Downloads are automatically organized in the following structure:
```
math_books/
├── arxiv/
│   └── [Category]_[Title].pdf
├── mit_ocw/
│   └── mit_[Title].pdf
└── gutenberg/
    └── gutenberg_[Title].pdf
```

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Open issues for bugs or feature requests
- Submit pull requests for improvements
- Suggest new document sources
- Help with documentation

## 📄 License

This project is open source and available under the MIT License.

## 🏷️ Tags

#mathematics #education #python #gui #pyside6 #arxiv #mit-ocw #project-gutenberg #textbooks #lecture-notes #academic-tools #educational-resources 