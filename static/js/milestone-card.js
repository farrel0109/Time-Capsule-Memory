/**
 * BabyGrow Milestone Card Generator
 * Creates shareable milestone cards using html2canvas
 */

class MilestoneCardGenerator {
    constructor() {
        this.templates = {
            default: {
                background: 'linear-gradient(135deg, #FCB9B2 0%, #B8B8DC 50%, #B5EAD7 100%)',
                textColor: '#5D4E37',
                accentColor: '#FCB9B2'
            },
            pink: {
                background: 'linear-gradient(135deg, #FCB9B2 0%, #FFECD2 100%)',
                textColor: '#5D4E37',
                accentColor: '#F9A099'
            },
            lavender: {
                background: 'linear-gradient(135deg, #B8B8DC 0%, #E8E8F4 100%)',
                textColor: '#5D4E37',
                accentColor: '#9999C9'
            },
            mint: {
                background: 'linear-gradient(135deg, #B5EAD7 0%, #E6F7F1 100%)',
                textColor: '#5D4E37',
                accentColor: '#67CEAD'
            }
        };
    }

    /**
     * Generate a milestone card
     * @param {Object} data - Card data
     * @param {string} data.childName - Child's name
     * @param {string} data.milestone - Milestone text
     * @param {string} data.date - Date achieved
     * @param {string} data.photoUrl - Optional photo URL
     * @param {string} template - Template name
     */
    async generateCard(data, template = 'default') {
        const cardEl = this.createCardElement(data, template);
        document.body.appendChild(cardEl);
        
        try {
            // Wait for images to load
            await this.waitForImages(cardEl);
            
            // Use html2canvas to capture
            const canvas = await html2canvas(cardEl, {
                backgroundColor: null,
                scale: 2,
                useCORS: true,
                logging: false
            });
            
            document.body.removeChild(cardEl);
            return canvas;
        } catch (error) {
            document.body.removeChild(cardEl);
            throw error;
        }
    }

    /**
     * Create the card DOM element
     */
    createCardElement(data, templateName) {
        const template = this.templates[templateName] || this.templates.default;
        
        const card = document.createElement('div');
        card.id = 'milestone-card-temp';
        card.style.cssText = `
            position: fixed;
            left: -9999px;
            top: 0;
            width: 400px;
            height: 500px;
            padding: 32px;
            background: ${template.background};
            border-radius: 24px;
            font-family: 'Quicksand', 'Nunito', sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            color: ${template.textColor};
        `;
        
        card.innerHTML = `
            <div style="font-size: 48px; margin-bottom: 16px;">🌟</div>
            
            ${data.photoUrl ? `
                <div style="
                    width: 120px;
                    height: 120px;
                    border-radius: 50%;
                    overflow: hidden;
                    border: 4px solid white;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                ">
                    <img src="${data.photoUrl}" style="width: 100%; height: 100%; object-fit: cover;" crossorigin="anonymous">
                </div>
            ` : ''}
            
            <h2 style="
                font-size: 28px;
                font-weight: 700;
                margin: 0 0 8px 0;
                color: ${template.textColor};
            ">${data.childName}</h2>
            
            <div style="
                font-size: 14px;
                color: ${template.accentColor};
                margin-bottom: 24px;
                text-transform: uppercase;
                letter-spacing: 2px;
            ">Milestone Tercapai!</div>
            
            <div style="
                background: rgba(255,255,255,0.9);
                padding: 20px 32px;
                border-radius: 16px;
                margin-bottom: 24px;
                max-width: 320px;
            ">
                <p style="
                    font-size: 22px;
                    font-weight: 600;
                    margin: 0;
                    line-height: 1.4;
                ">${data.milestone}</p>
            </div>
            
            <div style="
                font-size: 16px;
                color: ${template.textColor};
                opacity: 0.8;
            ">📅 ${data.date}</div>
            
            <div style="
                position: absolute;
                bottom: 16px;
                font-size: 12px;
                opacity: 0.5;
            ">🍼 BabyGrow</div>
        `;
        
        return card;
    }

    /**
     * Wait for all images in element to load
     */
    waitForImages(element) {
        const images = element.querySelectorAll('img');
        const promises = Array.from(images).map(img => {
            if (img.complete) return Promise.resolve();
            return new Promise((resolve, reject) => {
                img.onload = resolve;
                img.onerror = resolve; // Continue even if image fails
            });
        });
        return Promise.all(promises);
    }

    /**
     * Download the generated card
     */
    downloadCard(canvas, filename = 'milestone-card.png') {
        const link = document.createElement('a');
        link.download = filename;
        link.href = canvas.toDataURL('image/png');
        link.click();
    }

    /**
     * Share the card using Web Share API
     */
    async shareCard(canvas, data) {
        try {
            // Convert canvas to blob
            const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
            
            if (navigator.share && navigator.canShare) {
                const file = new File([blob], 'milestone-card.png', { type: 'image/png' });
                const shareData = {
                    title: `${data.childName} - Milestone`,
                    text: `🌟 ${data.childName} berhasil: ${data.milestone}!`,
                    files: [file]
                };
                
                if (navigator.canShare(shareData)) {
                    await navigator.share(shareData);
                    return true;
                }
            }
            
            // Fallback: download
            this.downloadCard(canvas, `milestone-${data.childName.replace(/\s+/g, '-')}.png`);
            return false;
        } catch (error) {
            console.error('Share failed:', error);
            this.downloadCard(canvas);
            return false;
        }
    }
}

// Global instance
window.MilestoneCard = new MilestoneCardGenerator();

/**
 * Quick function to generate and download a milestone card
 * @param {string} childName 
 * @param {string} milestone 
 * @param {string} date 
 * @param {string} photoUrl 
 * @param {string} template 
 */
async function generateMilestoneCard(childName, milestone, date, photoUrl = null, template = 'default') {
    try {
        const data = { childName, milestone, date, photoUrl };
        const canvas = await window.MilestoneCard.generateCard(data, template);
        window.MilestoneCard.downloadCard(canvas, `milestone-${childName.replace(/\s+/g, '-')}.png`);
        
        // Show success message
        if (window.BabyGrowCelebrate) {
            window.BabyGrowCelebrate.showBadge('📸 Kartu berhasil dibuat!', '✨');
        }
        return true;
    } catch (error) {
        console.error('Failed to generate card:', error);
        alert('Gagal membuat kartu. Silakan coba lagi.');
        return false;
    }
}

/**
 * Share milestone card
 */
async function shareMilestoneCard(childName, milestone, date, photoUrl = null, template = 'default') {
    try {
        const data = { childName, milestone, date, photoUrl };
        const canvas = await window.MilestoneCard.generateCard(data, template);
        await window.MilestoneCard.shareCard(canvas, data);
        return true;
    } catch (error) {
        console.error('Failed to share card:', error);
        return false;
    }
}
