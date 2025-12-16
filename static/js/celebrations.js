/**
 * BabyGrow Celebrations Library
 * Confetti, animations, and celebrations for special moments
 */

// Canvas Confetti configuration
const celebrationColors = {
    peach: ['#FFECD2', '#FFE0B5', '#FFCF9E'],
    pink: ['#FCB9B2', '#FCCFC9', '#F9A099'],
    lavender: ['#B8B8DC', '#D1D1E8', '#9999C9'],
    mint: ['#B5EAD7', '#CDF0E3', '#67CEAD'],
    rainbow: ['#FCB9B2', '#B8B8DC', '#B5EAD7', '#FFECD2', '#FFD166']
};

/**
 * Fire confetti celebration
 * @param {string} type - 'seal', 'milestone', 'open', or 'default'
 */
function celebrate(type = 'default') {
    if (typeof confetti === 'undefined') {
        console.warn('Confetti library not loaded');
        return;
    }
    
    const defaults = {
        origin: { y: 0.7 },
        zIndex: 9999
    };
    
    switch(type) {
        case 'seal':
            // Seal capsule - elegant burst
            confetti({
                ...defaults,
                particleCount: 100,
                spread: 70,
                colors: celebrationColors.lavender,
                shapes: ['circle']
            });
            // Add stars
            setTimeout(() => {
                confetti({
                    ...defaults,
                    particleCount: 50,
                    spread: 100,
                    colors: celebrationColors.pink,
                    shapes: ['star']
                });
            }, 200);
            break;
            
        case 'open':
            // Open capsule - big celebration!
            const duration = 3000;
            const animationEnd = Date.now() + duration;
            
            const interval = setInterval(() => {
                const timeLeft = animationEnd - Date.now();
                if (timeLeft <= 0) {
                    return clearInterval(interval);
                }
                
                confetti({
                    particleCount: 3,
                    angle: 60,
                    spread: 55,
                    origin: { x: 0 },
                    colors: celebrationColors.rainbow,
                    zIndex: 9999
                });
                confetti({
                    particleCount: 3,
                    angle: 120,
                    spread: 55,
                    origin: { x: 1 },
                    colors: celebrationColors.rainbow,
                    zIndex: 9999
                });
            }, 50);
            break;
            
        case 'milestone':
            // Milestone achieved - quick burst with badge effect
            confetti({
                ...defaults,
                particleCount: 60,
                spread: 90,
                colors: celebrationColors.mint,
                origin: { y: 0.6 }
            });
            // Show badge toast
            showBadge('🌟 Milestone Tercapai!');
            break;
            
        case 'growth':
            // Growth record added
            confetti({
                ...defaults,
                particleCount: 30,
                spread: 60,
                colors: celebrationColors.peach
            });
            break;
            
        default:
            confetti({
                ...defaults,
                particleCount: 50,
                spread: 60,
                colors: celebrationColors.rainbow
            });
    }
}

/**
 * Show a badge/toast notification
 * @param {string} message - Badge message
 * @param {string} icon - Emoji icon
 */
function showBadge(message, icon = '🎉') {
    // Create badge element
    const badge = document.createElement('div');
    badge.className = 'celebration-badge';
    badge.innerHTML = `
        <div class="badge-icon">${icon}</div>
        <div class="badge-message">${message}</div>
    `;
    
    // Add styles if not present
    if (!document.getElementById('celebration-styles')) {
        const styles = document.createElement('style');
        styles.id = 'celebration-styles';
        styles.textContent = `
            .celebration-badge {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) scale(0);
                background: linear-gradient(135deg, #FCB9B2, #B8B8DC);
                color: white;
                padding: 24px 48px;
                border-radius: 24px;
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 12px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                z-index: 10000;
                animation: badgePopIn 0.5s ease forwards;
            }
            
            .badge-icon {
                font-size: 4rem;
                animation: badgeBounce 0.5s ease 0.3s;
            }
            
            .badge-message {
                font-size: 1.5rem;
                font-weight: bold;
                text-align: center;
            }
            
            @keyframes badgePopIn {
                0% { transform: translate(-50%, -50%) scale(0); }
                50% { transform: translate(-50%, -50%) scale(1.1); }
                100% { transform: translate(-50%, -50%) scale(1); }
            }
            
            @keyframes badgeBounce {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-10px); }
            }
            
            @keyframes badgeFadeOut {
                to { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
            }
        `;
        document.head.appendChild(styles);
    }
    
    document.body.appendChild(badge);
    
    // Remove after animation
    setTimeout(() => {
        badge.style.animation = 'badgeFadeOut 0.3s ease forwards';
        setTimeout(() => badge.remove(), 300);
    }, 2000);
}

/**
 * Trigger celebration on page load if needed
 */
function checkCelebration() {
    const urlParams = new URLSearchParams(window.location.search);
    const celebrationType = urlParams.get('celebrate');
    
    if (celebrationType) {
        setTimeout(() => celebrate(celebrationType), 500);
    }
}

// Auto-check on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', checkCelebration);
} else {
    checkCelebration();
}

// Export for use
window.BabyGrowCelebrate = {
    celebrate,
    showBadge
};
