import logger from './logger';

// File Upload and Image Display Management
class ArtCloakApp {
    // DOM Elements
    private dropArea: HTMLElement;
    private fileInput: HTMLInputElement;
    private previewContainer: HTMLElement;
    private previewImage: HTMLImageElement;
    private styleInput: HTMLInputElement;
    private uploadButton: HTMLElement;
    private clearButton: HTMLElement;
    private resultContainer: HTMLElement;
    private originalImage: HTMLImageElement;
    private resultImage: HTMLImageElement;
    private downloadLink: HTMLAnchorElement;
    private newTransformButton: HTMLElement;
    private loadingContainer: HTMLElement;
    private statusMessage: HTMLElement;
    private progressBar: HTMLElement;
    
    // Selected file
    private selectedFile: File | null = null;
    
    // Get API URL from environment variable or fallback to localhost
    private readonly apiBaseUrl: string = process.env.ARTCLOAK_API_URL ? 
        process.env.ARTCLOAK_API_URL as string : 'http://localhost:8080';
    
    // API endpoint for image generation
    private readonly apiEndpoint: string = `${this.apiBaseUrl}/generate/`;
    
    constructor() {
        // Log the API URL being used
        console.log('ArtCloak initialized with API URL:', this.apiBaseUrl);
        console.log('API endpoint for image generation:', this.apiEndpoint);
        
        // Initialize DOM elements
        this.dropArea = document.getElementById('drop-area') as HTMLElement;
        this.fileInput = document.getElementById('file-input') as HTMLInputElement;
        this.previewContainer = document.getElementById('preview-container') as HTMLElement;
        this.previewImage = document.getElementById('preview-image') as HTMLImageElement;
        this.styleInput = document.getElementById('style-input') as HTMLInputElement;
        this.uploadButton = document.getElementById('upload-button') as HTMLElement;
        this.clearButton = document.getElementById('clear-button') as HTMLElement;
        this.resultContainer = document.getElementById('result-container') as HTMLElement;
        this.originalImage = document.getElementById('original-image') as HTMLImageElement;
        this.resultImage = document.getElementById('result-image') as HTMLImageElement;
        this.downloadLink = document.getElementById('download-link') as HTMLAnchorElement;
        this.newTransformButton = document.getElementById('new-transform-button') as HTMLElement;
        this.loadingContainer = document.getElementById('loading-container') as HTMLElement;
        this.statusMessage = document.getElementById('status-message') as HTMLElement;
        this.progressBar = document.getElementById('progress-bar') as HTMLElement;
        
        // Log the API endpoint being used
        console.log('Using API endpoint:', this.apiEndpoint);
        
        // Initialize event listeners
        this.initializeEventListeners();
    }
    
    // No auto-detection, using hardcoded API endpoint
    
    private initializeEventListeners(): void {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.dropArea.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });
        
        // Highlight drop area when file is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            this.dropArea.addEventListener(eventName, this.highlight.bind(this), false);
        });
        
        // Remove highlight when file leaves drop area
        ['dragleave', 'drop'].forEach(eventName => {
            this.dropArea.addEventListener(eventName, this.unhighlight.bind(this), false);
        });
        
        // Handle dropped files
        this.dropArea.addEventListener('drop', this.handleDrop.bind(this), false);
        
        // Handle file selection via input
        this.fileInput.addEventListener('change', this.handleFileSelect.bind(this), false);
        
        // Handle upload button click
        this.uploadButton.addEventListener('click', this.uploadImage.bind(this), false);
        
        // Handle clear button click
        this.clearButton.addEventListener('click', this.clearSelection.bind(this), false);
        
        // Handle new transform button click
        this.newTransformButton.addEventListener('click', this.startNewTransform.bind(this), false);
    }
    
    private preventDefaults(e: Event): void {
        e.preventDefault();
        e.stopPropagation();
    }
    
    private highlight(): void {
        this.dropArea.classList.add('highlight');
    }
    
    private unhighlight(): void {
        this.dropArea.classList.remove('highlight');
    }
    
    private handleDrop(e: DragEvent): void {
        const dt = e.dataTransfer;
        if (dt) {
            const files = dt.files;
            if (files.length > 0) {
                this.handleFiles(files);
            }
        }
    }
    
    private handleFileSelect(e: Event): void {
        const target = e.target as HTMLInputElement;
        if (target.files && target.files.length > 0) {
            this.handleFiles(target.files);
        }
    }
    
    private handleFiles(files: FileList): void {
        // Only process the first file
        const file = files[0];
        
        // Check if file is an image
        if (!file.type.match('image.*')) {
            alert('Please select an image file (JPEG or PNG)');
            return;
        }
        
        this.selectedFile = file;
        
        // Display preview
        const reader = new FileReader();
        reader.onload = (e: ProgressEvent<FileReader>) => {
            if (e.target?.result) {
                this.previewImage.src = e.target.result as string;
                this.previewContainer.classList.remove('hidden');
            }
        };
        reader.readAsDataURL(file);
    }
    
    private clearSelection(): void {
        this.selectedFile = null;
        this.previewImage.src = '';
        this.previewContainer.classList.add('hidden');
        this.fileInput.value = '';
    }
    
    // Simulates progress for better user experience during API call
    private progressInterval: number | null = null;
    
    private simulateProgress(): void {
        // Clear any existing interval
        if (this.progressInterval) {
            window.clearInterval(this.progressInterval);
        }
        
        let progress = 0;
        
        // Update progress every 1000ms (1 second) for a slower animation
        this.progressInterval = window.setInterval(() => {
            // Slow down progress significantly to account for longer processing time (up to 2 minutes)
            const increment = progress < 30 ? 1 : 
                             progress < 60 ? 0.5 : 
                             progress < 85 ? 0.3 : 0.1;
                             
            progress = Math.min(progress + increment, 90);
            
            // Update the progress bar
            this.progressBar.style.width = `${progress}%`;
            
            // Update status message at certain points
            if (progress > 10 && progress < 12) {
                this.statusMessage.textContent = "Analyzing image...";
            } else if (progress > 40 && progress < 42) {
                this.statusMessage.textContent = "Applying transformation...";
            } else if (progress > 70 && progress < 72) {
                this.statusMessage.textContent = "Generating final image...";
            } else if (progress > 85 && progress < 87) {
                this.statusMessage.textContent = "Almost done...";
            }
            
        }, 1000);
    }
    
    private stopProgressSimulation(): void {
        if (this.progressInterval) {
            window.clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
        
        // Set to 100% when complete
        this.progressBar.style.width = '100%';
    }
    
    private async uploadImage(): Promise<void> {
        if (!this.selectedFile) {
            alert('Please select an image first');
            return;
        }
        
        // Get the style from input
        const style = this.styleInput.value.trim() || 'studio ghibli';
        
        // Create the prompt
        const prompt = `re-create this image in the style of ${style}`;
        
        // Reset and show loading state
        this.progressBar.style.width = '0%';
        this.statusMessage.textContent = `Preparing to transform image in ${style} style...`;
        this.loadingContainer.classList.remove('hidden');
        this.previewContainer.classList.add('hidden');
        
        // Start progress simulation
        this.simulateProgress();
        
        // Using hardcoded API endpoint
        this.statusMessage.textContent = 'Connecting to API server...';
        
        try {
            // Create form data
            const formData = new FormData();
            // Ensure the file has a proper name and extension
            const fileName = this.selectedFile.name || 'image.jpg';
            
            // Use a Blob with correct type
            const fileBlob = new Blob([this.selectedFile], { type: this.selectedFile.type });
            const file = new File([fileBlob], fileName, { type: this.selectedFile.type });
            
            formData.append('file', file);
            formData.append('prompt', prompt);
            
            // Log the request for debugging
            logger.log('Sending request to API', { 
                endpoint: this.apiEndpoint,
                prompt: prompt,
                fileName: fileName,
                fileType: this.selectedFile.type,
                fileSize: this.selectedFile.size
            });
            
            this.statusMessage.textContent = `Sending image to API for ${style} transformation...`;
            
            // Create a timeout promise to handle long-running requests (2 minutes)
            const timeout = new Promise<Response>((_, reject) => {
                setTimeout(() => reject(new Error('Request timed out after 2 minutes')), 120000);
            });
            
            // Log for debug
            console.log(`Sending request to: ${this.apiEndpoint}`);
            console.log(`FormData contents: file (${fileName}), prompt: "${prompt}"`);
            
            // Send request to API with better CORS settings
            const fetchPromise = fetch(this.apiEndpoint, {
                method: 'POST',
                body: formData,
                mode: 'cors',
                credentials: 'omit', // Changed from same-origin 
                cache: 'no-cache',
                redirect: 'follow',
                headers: {
                    // Don't set Content-Type with FormData, browsers will set it with boundary
                    'Accept': 'image/png, image/jpeg, application/json'
                }
            });
            
            // Use Promise.race to handle timeouts
            const response = await Promise.race([fetchPromise, timeout]) as Response;
            
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
            
            // Get the transformed image as blob
            const imageBlob = await response.blob();
            logger.log('Received image from API', { size: imageBlob.size });
            
            // Complete the progress bar animation
            this.stopProgressSimulation();
            this.statusMessage.textContent = "Transformation complete!";
            
            // Display results
            this.displayResult(imageBlob);
        } catch (error: unknown) {
            // Stop progress simulation
            this.stopProgressSimulation();
            
            // Hide loading and show preview again
            this.loadingContainer.classList.add('hidden');
            this.previewContainer.classList.remove('hidden');
            
            // More detailed error logging
            logger.error('Error transforming image', error);
            
            // Try to get more information about the error
            let errorMessage = 'Error transforming image. Please try again.';
            
            if (error instanceof Error) {
                errorMessage = `Error: ${error.message}`;
                
                // Check for network errors
                if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
                    errorMessage = 'Network error: Please check your connection and make sure the backend server is running.';
                } else if (error.message.includes('timed out')) {
                    errorMessage = 'Request timed out after 2 minutes. Image generation can take up to 2 minutes depending on complexity. Please try again or use a smaller image.';
                }
            }
            
            // Show a more informative error message
            alert(errorMessage);
        }
    }
    
    private displayResult(imageBlob: Blob): void {
        // Create URLs for original and transformed images
        const originalImageURL = URL.createObjectURL(this.selectedFile as Blob);
        const transformedImageURL = URL.createObjectURL(imageBlob);
        
        // Get the style from input
        const style = this.styleInput.value.trim() || 'studio-ghibli';
        const safeStyle = style.toLowerCase().replace(/\s+/g, '-');
        
        // Update image sources
        this.originalImage.src = originalImageURL;
        this.resultImage.src = transformedImageURL;
        
        // Update download link
        this.downloadLink.href = transformedImageURL;
        this.downloadLink.download = `${safeStyle}-style-${new Date().getTime()}.png`;
        
        // Hide loading and show result
        this.loadingContainer.classList.add('hidden');
        this.resultContainer.classList.remove('hidden');
    }
    
    private startNewTransform(): void {
        // Clear current selection
        this.clearSelection();
        
        // Hide result and show drop area
        this.resultContainer.classList.add('hidden');
        
        // Revoke object URLs to free memory
        if (this.originalImage.src) {
            URL.revokeObjectURL(this.originalImage.src);
        }
        if (this.resultImage.src) {
            URL.revokeObjectURL(this.resultImage.src);
        }
    }
}

// Initialize the app when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    new ArtCloakApp();
});