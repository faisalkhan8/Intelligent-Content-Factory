// Intelligent Content Factory - Interactive Frontend
// Handles user interactions and API communication

class ContentFactory {
    constructor() {
        this.apiBase = window.location.origin;
        this.currentWorkflow = null;
        this.init();
    }

    init() {
        this.bindEventListeners();
        this.showSection('generation');
    }

    bindEventListeners() {
        // Form submission
        document.getElementById('contentForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.generateContent();
        });

        // Action buttons
        document.getElementById('copyBtn').addEventListener('click', () => this.copyContent());
        document.getElementById('downloadBtn').addEventListener('click', () => this.downloadContent());
        document.getElementById('newContentBtn').addEventListener('click', () => this.startNew());
        document.getElementById('retryBtn').addEventListener('click', () => this.retryGeneration());
    }

    showSection(section) {
        // Hide all sections
        const sections = ['generation', 'progress', 'results', 'error'];
        sections.forEach(s => {
            const element = document.getElementById(`${s}Section`);
            if (element) element.style.display = 'none';
        });

        // Show target section
        const targetSection = document.getElementById(`${section}Section`);
        if (targetSection) {
            targetSection.style.display = 'block';
            targetSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    async generateContent() {
        const form = document.getElementById('contentForm');
        const formData = new FormData(form);
        
        const topic = formData.get('topic').trim();
        const contentType = formData.get('contentType');

        if (!topic) {
            this.showToast('Please enter a topic!', 'error');
            return;
        }

        // Disable form and show progress
        this.setFormEnabled(false);
        this.showSection('progress');
        this.startProgress();

        try {
            // Call the API
            const response = await fetch(`${this.apiBase}/api/v1/generate/?topic=${encodeURIComponent(topic)}&content_type=${contentType}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.success) {
                this.displayResults(result);
            } else {
                throw new Error(result.message || 'Content generation failed');
            }

        } catch (error) {
            console.error('Generation error:', error);
            this.showError(error.message);
        } finally {
            this.setFormEnabled(true);
        }
    }

    startProgress() {
        this.resetProgress();
        
        // Simulate multi-agent workflow
        setTimeout(() => this.updateProgress('research', 33), 1000);
        setTimeout(() => this.updateProgress('writing', 66), 8000);
        setTimeout(() => this.updateProgress('review', 100), 20000);
    }

    resetProgress() {
        const agents = ['research', 'writing', 'review'];
        agents.forEach(agent => {
            const progressEl = document.getElementById(`${agent}Progress`);
            const statusEl = document.getElementById(`${agent}Status`);
            
            progressEl.classList.remove('active', 'completed');
            statusEl.innerHTML = '<i class="fas fa-clock"></i>';
        });

        document.getElementById('progressFill').style.width = '0%';
        document.getElementById('progressText').textContent = 'Initializing...';
    }

    updateProgress(agent, percentage) {
        // Update specific agent
        const progressEl = document.getElementById(`${agent}Progress`);
        const statusEl = document.getElementById(`${agent}Status`);
        
        if (progressEl && statusEl) {
            progressEl.classList.add('active');
            statusEl.innerHTML = '<i class="fas fa-cog fa-spin"></i>';
            
            // Complete after some time
            setTimeout(() => {
                progressEl.classList.remove('active');
                progressEl.classList.add('completed');
                statusEl.innerHTML = '<i class="fas fa-check"></i>';
            }, 3000);
        }

        // Update overall progress
        document.getElementById('progressFill').style.width = `${percentage}%`;
        
        const messages = {
            33: 'Research phase complete...',
            66: 'Content creation in progress...',
            100: 'Quality review complete!'
        };
        
        document.getElementById('progressText').textContent = messages[percentage] || 'Processing...';
    }

    displayResults(result) {
        this.currentWorkflow = result.workflow_result;
        
        // Display content with proper Markdown rendering
        const contentDisplay = document.getElementById('contentDisplay');
        const formattedContent = this.renderMarkdown(result.workflow_result.content);
        contentDisplay.innerHTML = formattedContent;

        // Display stats
        if (result.workflow_result) {
            document.getElementById('agentsUsed').textContent = result.workflow_result.agents_used?.length || 'N/A';
            document.getElementById('tasksCompleted').textContent = result.workflow_result.tasks_completed || 'N/A';
            document.getElementById('executionTime').textContent = result.workflow_result.execution_time || 'N/A';
            document.getElementById('qualityScore').textContent = result.workflow_result.quality_score || 'N/A';
            
            document.getElementById('workflowStats').style.display = 'block';
        }

        this.showSection('results');
        this.showToast('Content generated successfully! 🎉');
    }

    renderMarkdown(text) {
        // Simple Markdown parser for basic formatting
        let html = text
            // Headers
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            
            // Bold text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/__(.*?)__/g, '<strong>$1</strong>')
            
            // Italic text
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/_(.*?)_/g, '<em>$1</em>')
            
            // Lists
            .replace(/^\* (.*$)/gm, '<li>$1</li>')
            .replace(/^- (.*$)/gm, '<li>$1</li>')
            
            // Line breaks
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');
            
        // Wrap lists in ul tags
        html = html.replace(/(<li>.*<\/li>)/gs, (match) => {
            return '<ul>' + match + '</ul>';
        });
        
        // Wrap in paragraphs
        if (!html.startsWith('<h') && !html.startsWith('<ul>')) {
            html = '<p>' + html + '</p>';
        }
        
        // Clean up multiple paragraph tags
        html = html.replace(/<\/p><p>/g, '</p>\n<p>');
        html = html.replace(/<p><\/p>/g, '');
        
        return html;
    }

    showError(message) {
        document.getElementById('errorMessage').textContent = message || 'An unexpected error occurred.';
        this.showSection('error');
        this.showToast('Generation failed. Please try again.', 'error');
    }

    async copyContent() {
        // Get the original content (not the HTML formatted version)
        const content = this.currentWorkflow?.content || document.getElementById('contentDisplay').textContent;
        
        try {
            await navigator.clipboard.writeText(content);
            this.showToast('Content copied to clipboard! 📋');
        } catch (error) {
            console.error('Copy failed:', error);
            this.showToast('Copy failed. Please select and copy manually.', 'error');
        }
    }

    downloadContent() {
        // Get the original content (not the HTML formatted version)
        const content = this.currentWorkflow?.content || document.getElementById('contentDisplay').textContent;
        const topic = document.getElementById('topic').value;
        
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `${topic.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_content.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.showToast('Content downloaded! 📥');
    }

    startNew() {
        // Reset form
        document.getElementById('contentForm').reset();
        
        // Show generation section
        this.showSection('generation');
        
        // Focus on topic input
        document.getElementById('topic').focus();
    }

    retryGeneration() {
        this.generateContent();
    }

    setFormEnabled(enabled) {
        const form = document.getElementById('contentForm');
        const inputs = form.querySelectorAll('input, select, button');
        
        inputs.forEach(input => {
            input.disabled = !enabled;
        });

        const generateBtn = document.getElementById('generateBtn');
        if (enabled) {
            generateBtn.innerHTML = '<i class="fas fa-rocket"></i> Generate Content';
        } else {
            generateBtn.innerHTML = '<div class="loading"></div> Generating...';
        }
    }

    showToast(message, type = 'success') {
        const toast = document.getElementById('toast');
        const toastMessage = document.getElementById('toastMessage');
        
        toastMessage.textContent = message;
        
        // Update toast style based on type
        toast.style.background = type === 'error' ? '#ef4444' : '#10b981';
        
        // Show toast
        toast.classList.add('show');
        
        // Hide after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ContentFactory();
});

// Handle any uncaught errors
window.addEventListener('error', (e) => {
    console.error('Application error:', e.error);
});

// Add some helpful utilities
window.ContentFactory = ContentFactory;