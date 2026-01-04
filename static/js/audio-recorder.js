/**
 * BabyGrow Audio Recorder
 * Records baby's first sounds with waveform visualization
 */

class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.audioContext = null;
        this.analyser = null;
        this.stream = null;
        this.isRecording = false;
        this.animationId = null;
    }

    /**
     * Initialize audio recording
     */
    async init() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.analyser = this.audioContext.createAnalyser();
            
            const source = this.audioContext.createMediaStreamSource(this.stream);
            source.connect(this.analyser);
            
            this.analyser.fftSize = 256;
            this.mediaRecorder = new MediaRecorder(this.stream);
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            return true;
        } catch (error) {
            console.error('Failed to initialize audio:', error);
            throw new Error('Tidak bisa mengakses mikrofon. Pastikan izin sudah diberikan.');
        }
    }

    /**
     * Start recording
     * @param {HTMLCanvasElement} canvas - Canvas for waveform visualization
     */
    start(canvas) {
        if (!this.mediaRecorder) {
            throw new Error('Audio recorder not initialized');
        }
        
        this.audioChunks = [];
        this.mediaRecorder.start(100);
        this.isRecording = true;
        
        if (canvas) {
            this.startVisualization(canvas);
        }
    }

    /**
     * Stop recording
     * @returns {Promise<Blob>} Audio blob
     */
    stop() {
        return new Promise((resolve) => {
            this.mediaRecorder.onstop = () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                resolve(audioBlob);
            };
            
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.stopVisualization();
        });
    }

    /**
     * Start waveform visualization
     */
    startVisualization(canvas) {
        const ctx = canvas.getContext('2d');
        const bufferLength = this.analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        
        const draw = () => {
            this.animationId = requestAnimationFrame(draw);
            
            this.analyser.getByteFrequencyData(dataArray);
            
            // Clear canvas with gradient
            const gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
            gradient.addColorStop(0, '#FFECD2');
            gradient.addColorStop(0.5, '#FCB9B2');
            gradient.addColorStop(1, '#B8B8DC');
            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Draw waveform bars
            const barWidth = (canvas.width / bufferLength) * 2.5;
            let x = 0;
            
            for (let i = 0; i < bufferLength; i++) {
                const barHeight = (dataArray[i] / 255) * canvas.height;
                
                // Gradient for bars
                const barGradient = ctx.createLinearGradient(0, canvas.height - barHeight, 0, canvas.height);
                barGradient.addColorStop(0, '#B5EAD7');
                barGradient.addColorStop(1, '#67CEAD');
                
                ctx.fillStyle = barGradient;
                ctx.fillRect(x, canvas.height - barHeight, barWidth - 1, barHeight);
                
                x += barWidth;
            }
        };
        
        draw();
    }

    /**
     * Stop visualization
     */
    stopVisualization() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
    }

    /**
     * Draw static waveform for playback
     */
    static drawStaticWaveform(canvas, audioBlob) {
        const ctx = canvas.getContext('2d');
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        const reader = new FileReader();
        reader.onload = async (e) => {
            try {
                const audioBuffer = await audioContext.decodeAudioData(e.target.result);
                const channelData = audioBuffer.getChannelData(0);
                
                // Clear canvas
                const gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
                gradient.addColorStop(0, '#FFECD2');
                gradient.addColorStop(0.5, '#B8B8DC');
                gradient.addColorStop(1, '#B5EAD7');
                ctx.fillStyle = gradient;
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                
                // Calculate samples per bar
                const samplesPerBar = Math.floor(channelData.length / canvas.width);
                const centerY = canvas.height / 2;
                
                ctx.strokeStyle = '#5D4E37';
                ctx.lineWidth = 2;
                ctx.beginPath();
                
                for (let i = 0; i < canvas.width; i++) {
                    const sampleIndex = i * samplesPerBar;
                    let max = 0;
                    
                    for (let j = 0; j < samplesPerBar; j++) {
                        const sample = Math.abs(channelData[sampleIndex + j] || 0);
                        if (sample > max) max = sample;
                    }
                    
                    const barHeight = max * canvas.height * 0.8;
                    
                    ctx.moveTo(i, centerY - barHeight / 2);
                    ctx.lineTo(i, centerY + barHeight / 2);
                }
                
                ctx.stroke();
            } catch (error) {
                console.error('Failed to draw waveform:', error);
            }
        };
        
        reader.readAsArrayBuffer(audioBlob);
    }

    /**
     * Cleanup resources
     */
    destroy() {
        this.stopVisualization();
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }
        if (this.audioContext) {
            this.audioContext.close();
        }
    }
}

// Global instance - only create AudioRecorder class, no conflicting global functions
window.BabyGrowRecorder = new AudioRecorder();
