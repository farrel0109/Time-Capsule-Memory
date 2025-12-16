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

// Global instance
window.BabyGrowRecorder = new AudioRecorder();

/**
 * Create a simple audio recorder UI
 * @param {HTMLElement} container - Container element
 * @param {Function} onSave - Callback when audio is saved
 */
function createAudioRecorderUI(container, onSave) {
    container.innerHTML = `
        <div class="audio-recorder-container" style="
            background: linear-gradient(135deg, var(--color-peach) 0%, var(--color-cloud) 100%);
            border-radius: var(--radius-lg);
            padding: var(--space-lg);
            text-align: center;
        ">
            <div style="font-size: 3rem; margin-bottom: var(--space-md);">🎙️</div>
            <h4 style="margin-bottom: var(--space-md);">Rekam Suara Si Kecil</h4>
            
            <canvas id="audio-waveform" width="300" height="80" style="
                border-radius: var(--radius-md);
                margin-bottom: var(--space-md);
                box-shadow: var(--shadow-soft);
            "></canvas>
            
            <div id="recording-status" style="
                font-size: 0.875rem;
                color: var(--color-text-muted);
                margin-bottom: var(--space-md);
            ">Klik tombol untuk mulai merekam</div>
            
            <div style="display: flex; gap: var(--space-md); justify-content: center;">
                <button id="record-btn" class="btn btn-primary" onclick="toggleRecording()">
                    <i class="bi bi-mic"></i> Mulai Rekam
                </button>
                <button id="play-btn" class="btn btn-secondary" style="display: none;" onclick="playRecording()">
                    <i class="bi bi-play"></i> Putar
                </button>
                <button id="save-btn" class="btn btn-success" style="display: none;" onclick="saveRecording()">
                    <i class="bi bi-save"></i> Simpan
                </button>
            </div>
            
            <audio id="audio-preview" style="display: none;"></audio>
        </div>
    `;
    
    window._audioRecorderOnSave = onSave;
}

let recordedBlob = null;

async function toggleRecording() {
    const btn = document.getElementById('record-btn');
    const status = document.getElementById('recording-status');
    const canvas = document.getElementById('audio-waveform');
    const playBtn = document.getElementById('play-btn');
    const saveBtn = document.getElementById('save-btn');
    
    try {
        if (!window.BabyGrowRecorder.isRecording) {
            // Start recording
            if (!window.BabyGrowRecorder.mediaRecorder) {
                await window.BabyGrowRecorder.init();
            }
            
            window.BabyGrowRecorder.start(canvas);
            btn.innerHTML = '<i class="bi bi-stop-fill"></i> Berhenti';
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-danger');
            status.textContent = '🔴 Sedang merekam...';
            playBtn.style.display = 'none';
            saveBtn.style.display = 'none';
        } else {
            // Stop recording
            recordedBlob = await window.BabyGrowRecorder.stop();
            
            btn.innerHTML = '<i class="bi bi-mic"></i> Rekam Ulang';
            btn.classList.remove('btn-danger');
            btn.classList.add('btn-primary');
            status.textContent = '✅ Rekaman selesai!';
            playBtn.style.display = 'inline-flex';
            saveBtn.style.display = 'inline-flex';
            
            // Draw static waveform
            AudioRecorder.drawStaticWaveform(canvas, recordedBlob);
            
            // Setup audio preview
            const audio = document.getElementById('audio-preview');
            audio.src = URL.createObjectURL(recordedBlob);
        }
    } catch (error) {
        status.textContent = '❌ ' + error.message;
        console.error(error);
    }
}

function playRecording() {
    const audio = document.getElementById('audio-preview');
    audio.play();
}

function saveRecording() {
    if (recordedBlob && window._audioRecorderOnSave) {
        window._audioRecorderOnSave(recordedBlob);
    }
}
