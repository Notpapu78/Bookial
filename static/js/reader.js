// Lector de libros digitales
class BookReader {
    constructor(bookId, pdfUrl) {
        this.bookId = bookId;
        this.pdfUrl = pdfUrl;
        this.currentPage = 1;
        this.totalPages = 0;
        this.zoom = 1.0;
        this.init();
    }
    
    init() {
        this.loadPDF();
        this.setupEventListeners();
        this.loadProgress();
    }
    
    loadPDF() {
        const loadingTask = pdfjsLib.getDocument(this.pdfUrl);
        loadingTask.promise.then((pdf) => {
            this.totalPages = pdf.numPages;
            document.getElementById('total-pages').textContent = this.totalPages;
            this.renderPage(this.currentPage, pdf);
        }).catch((error) => {
            console.error('Error loading PDF:', error);
            this.showError('No se pudo cargar el libro');
        });
    }
    
    renderPage(pageNum, pdf) {
        pdf.getPage(pageNum).then((page) => {
            const viewport = page.getViewport({ scale: this.zoom });
            const canvas = document.getElementById('book-canvas');
            const context = canvas.getContext('2d');
            
            canvas.height = viewport.height;
            canvas.width = viewport.width;
            
            const renderContext = {
                canvasContext: context,
                viewport: viewport
            };
            
            page.render(renderContext);
            this.updatePageInfo();
            this.saveProgress(pageNum);
        });
    }
    
    nextPage() {
        if (this.currentPage < this.totalPages) {
            this.currentPage++;
            this.loadPDF();
        }
    }
    
    prevPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.loadPDF();
        }
    }
    
    zoomIn() {
        if (this.zoom < 2.0) {
            this.zoom += 0.25;
            this.loadPDF();
        }
    }
    
    zoomOut() {
        if (this.zoom > 0.5) {
            this.zoom -= 0.25;
            this.loadPDF();
        }
    }
    
    saveProgress(pageNum) {
        localStorage.setItem(`book_${this.bookId}_progress`, pageNum);
        // Enviar al servidor
        fetch(`/api/save_progress/${this.bookId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ page: pageNum })
        });
    }
    
    loadProgress() {
        const savedPage = localStorage.getItem(`book_${this.bookId}_progress`);
        if (savedPage) {
            this.currentPage = parseInt(savedPage);
        }
    }
    
    updatePageInfo() {
        document.getElementById('current-page').textContent = this.currentPage;
    }
    
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger';
        errorDiv.textContent = message;
        document.querySelector('main').prepend(errorDiv);
    }
    
    setupEventListeners() {
        document.getElementById('next-page')?.addEventListener('click', () => this.nextPage());
        document.getElementById('prev-page')?.addEventListener('click', () => this.prevPage());
        document.getElementById('zoom-in')?.addEventListener('click', () => this.zoomIn());
        document.getElementById('zoom-out')?.addEventListener('click', () => this.zoomOut());
        
        // Teclado
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowRight') this.nextPage();
            if (e.key === 'ArrowLeft') this.prevPage();
        });
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    const bookElement = document.getElementById('book-reader');
    if (bookElement) {
        const bookId = bookElement.dataset.bookId;
        const pdfUrl = bookElement.dataset.pdfUrl;
        new BookReader(bookId, pdfUrl);
    }
});