console.log("🚀 script_app.js v3.9 - ONCE-ONLY LEAD MODAL...");

// 0. AGGRESSIVE CSS INJECTION FOR GOOGLE MAPS INFOWINDOW (FIX FOR REMOTE CACHING)
(function injectStyles() {
    const styleId = 'google-maps-iw-fix';
    if (document.getElementById(styleId)) return;

    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = `
        /* Remove whitespace and padding from Google Maps InfoWindow default bubble */
        .gm-style-iw-c {
            padding: 0 !important;
            max-width: none !important;
            max-height: none !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15) !important;
        }
        .gm-style-iw-d {
            overflow: hidden !important;
            padding: 0 !important;
            margin: 0 !important;
            max-width: none !important;
            max-height: none !important;
        }
        /* Custom content inside the InfoWindow */
        .iw-content-v27 {
            padding: 12px !important;
            margin: 0 !important;
            width: 300px !important;
            box-sizing: border-box !important;
            display: flex !important;
            flex-direction: column !important;
            font-family: 'Inter', sans-serif !important;
        }
        .iw-content-v27.is-mobile { width: 250px !important; }
        .iw-title {
            font-size: 16px !important;
            font-weight: 800 !important;
            color: #1a73e8 !important;
            margin: 0 0 2px 0 !important;
            line-height: 1.2 !important;
            display: block !important;
        }
        .iw-expertise {
            font-size: 11px !important;
            color: #666 !important;
            line-height: 1.3 !important;
            margin: 0 0 5px 0 !important;
            display: block !important;
        }
        .iw-knowledge {
            margin-top: 8px !important;
            border-top: 1px dashed #eee !important;
            padding-top: 8px !important;
            display: flex !important;
            gap: 10px !important;
            align-items: center !important;
        }
        .iw-expert-avatar {
            width: 50px !important;
            height: 50px !important;
            object-fit: cover !important;
            border-radius: 50% !important;
            flex-shrink: 0 !important;
        }
        .iw-topic-info { flex: 1 !important; overflow: hidden !important; }
        .iw-topic-name {
            font-size: 12px !important;
            font-weight: 600 !important;
            color: #333 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }
        .iw-topic-status {
            font-size: 14px !important;
            font-weight: 700 !important;
            color: #1a73e8 !important;
        }
        /* Fix close button position */
        .gm-ui-hover-effect {
            top: 2px !important;
            right: 2px !important;
            background: rgba(255,255,255,0.9) !important;
            border-radius: 50% !important;
        }
    `;
    document.head.appendChild(style);
})();

// DUAL ACTION: Join Group + Chat with Admin/Staff
// Global function to be accessible by onclick handlers
function handleDualZaloAction(groupLink, topicName, staffZalo) {
    // 1. Prepare Admin Chat Link (Deep Link)
    // If staffZalo is provided (from Link NV), use it. Otherwise placeholder or skip.
    // If staffZalo is missing or invalid, we prioritize Group Link only.

    let adminChatLink = "";

    if (staffZalo && staffZalo.length > 8) {
        const msg = encodeURIComponent(`Chào bạn, tôi quan tâm chủ đề tri thức: ${topicName}. Nhờ hỗ trợ!`);
        adminChatLink = `https://zalo.me/${staffZalo}?text=${msg}`;
    }

    // DEBUG: Log to Console only (User Request)
    console.log("Dual Action Debug:", { groupLink, staffZalo, adminChatLink });

    // SEQUENCING FOR UX (User Verified):
    // 1. Open Group Link (Background Context)
    const win1 = window.open(groupLink, '_blank');

    // 2. Open Staff Chat (Foreground Action)
    if (adminChatLink) {
        // Try opening second tab
        const win2 = window.open(adminChatLink, '_blank');

        if (!win2 || win2.closed || typeof win2.closed == 'undefined') {
            renderMessage('ai', '<i class="material-icons" style="color:#f57f17; vertical-align:bottom;">warning</i> <b>LỖI CHẶN POP-UP!</b><br>Máy tính đã chặn cửa sổ Chat Nhân Viên. Vui lòng bấm vào icon [Pop-up] trên thanh địa chỉ và chọn "Always Allow" (Luôn cho phép).', true);
        } else {
            console.log("Dual Action: Group -> Staff Chat (Success)");
        }
    } else {
        renderMessage('ai', '<i class="material-icons" style="color:#f57f17; vertical-align:bottom;">warning</i> <b>LỖI DỮ LIỆU:</b> Không tìm thấy số Zalo nhân viên (Link NV).', true);
    }
}

let map;
let userMarker;
let expertMarkers = []; // Array of google.maps.Marker
let expertInfoWindows = []; // FIX 2: Track all InfoWindow instances
let currentUserLocation = null;
let googleMapsLoaded = false;
let chatHistory = []; // Global history array
window.lastSearchTime = Date.now(); // Global context timer
window.interestedTopics = JSON.parse(localStorage.getItem('interestedTopics') || '[]'); // Accumulate topics user is interested in
function saveInterestedTopics() {
    localStorage.setItem('interestedTopics', JSON.stringify(window.interestedTopics));
}

// Helper to load Google Maps script dynamically
function loadGoogleMaps(apiKey) {
    if (googleMapsLoaded) return Promise.resolve();

    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places`;
        script.async = true;
        script.defer = true;
        script.onload = () => {
            googleMapsLoaded = true;
            console.log("📍 Google Maps API Loaded.");
            resolve();
        };
        script.onerror = reject;
        document.head.appendChild(script);
    });
}


// Configure Markdown renderer safely
if (typeof marked !== 'undefined') {
    const renderer = new marked.Renderer();
    renderer.link = function (href, title, text) {
        // Prevent undefined hrefs if possible, though strictness is good
        if (!href || href === 'undefined' || href === 'null') href = '#';
        return `<a href="${href}" title="${title || ''}" target="_self">${text}</a>`;
    };
    marked.setOptions({ renderer: renderer });
}

// --- Chat History Persistence ---
function getStorage() {
    // We use sessionStorage for all users' chat history to ensure privacy on shared devices.
    // This persists during same-tab navigation but clears when the tab is closed.
    return sessionStorage;
}

function getHistoryKey() {
    const sessionId = localStorage.getItem('session_id') || 'guest';
    return `chat_history_${sessionId}`;
}

function saveHistory() {
    const storage = getStorage();
    storage.setItem(getHistoryKey(), JSON.stringify(chatHistory));
}

function loadHistory() {
    const storage = getStorage();
    const saved = storage.getItem(getHistoryKey());
    if (saved) {
        try {
            chatHistory = JSON.parse(saved);
            chatHistory.forEach(item => {
                if (item.type === 'message') {
                    renderMessage(item.sender, item.text, false);
                } else if (item.type === 'experts' || item.type === 'stores') {
                    renderExpertCards(item.data, false);
                }
            });
        } catch (e) {
            console.error("Error loading history:", e);
            chatHistory = [];
        }
    }
}

// Inject CSS for Store Cards
// Styles moved to style.css for cleaner separation and easier maintenance.
// const style = document.createElement('style'); ... (removed)

// 3.1. Khởi tạo Bản đồ (Map Initialization - Google Maps)
async function initializeMap() {
    if (!googleMapsLoaded) {
        console.warn("Map: Library not loaded yet.");
        return;
    }

    const mapOptions = {
        center: { lat: 10.762622, lng: 106.660172 }, // HCMC
        zoom: 13,
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: false,
        styles: [
            {
                "featureType": "all",
                "elementType": "labels.text.fill",
                "stylers": [{ "color": "#7c93a3" }]
            }
        ]
    };

    map = new google.maps.Map(document.getElementById('map-container'), mapOptions);
}

function updateMap(userLat, userLng, experts) {
    if (!map || !googleMapsLoaded) return;

    // 1. Handle User Marker
    if (userMarker) {
        userMarker.setMap(null);
    }

    const isMobile = window.innerWidth <= 768;

    if (userLat && userLng) {
        const userPos = { lat: parseFloat(userLat), lng: parseFloat(userLng) };

        const userIcon = {
            url: "http://maps.google.com/mapfiles/ms/icons/red-dot.png"
        };

        userMarker = new google.maps.Marker({
            position: userPos,
            map: map,
            title: "Vị trí của bạn",
            icon: userIcon
        });

        const infoWindow = new google.maps.InfoWindow({
            content: "<b>Vị trí của bạn</b>"
        });
        userMarker.addListener("click", () => infoWindow.open(map, userMarker));

        map.panTo(userPos);
        // FIX: Reset zoom if no experts are found, to avoid staying zoomed out from previous fitBounds
        if (!experts || experts.length === 0) {
            map.setZoom(13);
        }
    }

    // 2. Handle Expert Markers
    if (experts !== null) {
        // Clear old markers and InfoWindows
        expertMarkers.forEach(m => m.setMap(null));
        expertMarkers = [];
        expertInfoWindows.forEach(iw => iw.close());
        expertInfoWindows = [];

        if (experts.length > 0) {
            const bounds = new google.maps.LatLngBounds();
            if (userLat && userLng) bounds.extend({ lat: parseFloat(userLat), lng: parseFloat(userLng) });

            experts.forEach((expert, index) => {
                const expertPos = { lat: parseFloat(expert.lat), lng: parseFloat(expert.lng) };

                // Get first topic if available for the popup
                const firstTopic = (expert.topics && expert.topics.length > 0) ? expert.topics[0] : null;

                // Premium Zalo Button for InfoWindow
                const zaloLink = expert.zalo_link ?
                    `<a href="${expert.zalo_link}" target="_blank" class="zalo-btn">
                        <i class="material-icons" style="font-size:18px; margin-right:6px;">groups</i>
                        <span>Tham gia cộng đồng</span>
                    </a>` : '';

                if (isMobile) {
                    infoWindowContent = `
                        <div class="iw-content-v27 is-mobile">
                            <b class="iw-title">${expert.name}</b>
                            <div class="iw-expertise">${expert.expertise}</div>
                            ${zaloLink}
                        </div>
                    `;
                } else {
                    let knowledgeHtml = '';
                    if (firstTopic) {
                        knowledgeHtml = `
                            <div class="iw-knowledge">
                                <img src="${expert.avatar_url || 'assets/expert-default.jpg'}" class="iw-expert-avatar">
                                <div class="iw-topic-info">
                                    <div class="iw-topic-name">${firstTopic.name}</div>
                                    <div class="iw-topic-status">Chủ đề tri thức</div>
                                </div>
                            </div>
                        `;
                    }

                    infoWindowContent = `
                        <div class="iw-content-v27 is-desktop">
                            <b class="iw-title">${expert.name}</b>
                            <div class="iw-expertise">${expert.expertise}</div>
                            ${knowledgeHtml}
                            ${zaloLink}
                        </div>
                    `;
                }

                const expertIcon = {
                    url: "http://maps.google.com/mapfiles/ms/icons/blue-dot.png"
                };

                const marker = new google.maps.Marker({
                    position: expertPos,
                    map: map,
                    title: expert.name,
                    icon: expertIcon
                });

                const infoWindow = new google.maps.InfoWindow({
                    content: infoWindowContent
                });

                // FIX 2: Store InfoWindow instance for later control
                expertInfoWindows.push(infoWindow);

                marker.addListener("click", () => {
                    expertInfoWindows.forEach(iw => {
                        if (iw !== infoWindow) iw.close();
                    });
                    infoWindow.open(map, marker);
                });

                // TỰ ĐỘNG MỞ InfoWindow cho TẤT CẢ các chuyên gia ngay khi có kết quả
                setTimeout(() => {
                    infoWindow.open(map, marker);
                }, 500 + (index * 150));

                expertMarkers.push(marker);
                bounds.extend(expertPos);
            });

            // Auto fit bounds
            map.fitBounds(bounds);
            // Limit zoom if only 1 marker
            if (experts.length === 1 && (!userLat || !userLng)) {
                google.maps.event.addListenerOnce(map, 'bounds_changed', () => {
                    if (map.getZoom() > 15) map.setZoom(15);
                });
            }
        }
    }
}

/**
 * Focuses the map on a specific store and opens its info window.
 * Used when clicking on store cards in the chat.
 */
function focusOnExpert(lat, lng, name) {
    if (!map || !googleMapsLoaded) return;

    const pos = { lat: parseFloat(lat), lng: parseFloat(lng) };

    // Close all expert InfoWindows first to ensure clean focus
    expertInfoWindows.forEach(iw => iw.close());

    // Smoothly pan to the location
    map.panTo(pos);
    map.setZoom(17);

    // Find the marker for this expert and trigger a click to show InfoWindow
    const marker = expertMarkers.find(m => {
        const mPos = m.getPosition();
        return Math.abs(mPos.lat() - pos.lat) < 0.0001 && Math.abs(mPos.lng() - pos.lng) < 0.0001;
    });

    if (marker) {
        // Trigger click will open only this InfoWindow (others already closed)
        google.maps.event.trigger(marker, 'click');
    }
}



// --- Geolocation Logic ---
let isLocating = false;

function getUserLocation(isAutoTriggered = false) {
    if (isLocating) {
        console.log("GPS: Request already in progress, returning current state...");
        return Promise.resolve(currentUserLocation);
    }

    return new Promise((resolve) => {
        if (!navigator.geolocation) {
            console.warn("GPS: Geolocation not supported.");
            resolve(null);
            return;
        }

        isLocating = true;
        let watchId = null;
        let bestPosition = null;
        let hasResolved = false;

        const stopWatching = () => {
            if (watchId !== null) {
                navigator.geolocation.clearWatch(watchId);
                watchId = null;
            }
            isLocating = false;
        };

        const currentOptions = {
            enableHighAccuracy: true,
            timeout: 8000,
            maximumAge: 0 // Always check fresh hardware
        };

        // FINAL RESOLVE: Only called once
        const finish = (pos) => {
            if (hasResolved) return;
            hasResolved = true;
            stopWatching();

            if (pos) {
                currentUserLocation = { lat: pos.coords.latitude, lng: pos.coords.longitude };
                sessionStorage.setItem('last_location', JSON.stringify(currentUserLocation));
                sessionStorage.setItem('last_location_acc', pos.coords.accuracy.toFixed(0));
                updateMap(currentUserLocation.lat, currentUserLocation.lng, null);
                console.log(`GPS: Finalized with Acc: ${pos.coords.accuracy.toFixed(1)}m`);
                resolve(currentUserLocation);
            } else {
                console.warn("GPS: Timeout/No position found.");
                resolve(null);
            }
        };

        // EMERGENCY TIMEOUT: If nothing happens in 4s, just give up
        const timer = setTimeout(() => {
            console.log("GPS: Emergency timeout reached.");
            finish(bestPosition);
        }, isAutoTriggered ? 2000 : 4000);

        watchId = navigator.geolocation.watchPosition(
            (position) => {
                const acc = position.coords.accuracy;
                console.log(`GPS: Reading - Acc: ${acc.toFixed(1)}m`);

                if (!bestPosition || acc < bestPosition.coords.accuracy) {
                    bestPosition = position;
                }

                // SPEED OPTIMIZATION:
                // 1. If we hit high precision (< 35m), finish INSTANTLY.
                if (acc < 35) {
                    console.log("GPS: High precision hit! Resolving instantly.");
                    clearTimeout(timer);
                    finish(position);
                    return;
                }
            },
            (error) => {
                console.warn("GPS: Provider error:", error.code);
                if (error.code === 1) { // Denied
                    clearTimeout(timer);
                    finish(null);
                }
            },
            currentOptions
        );

        // EXTRA SPEED: If we haven't hit <35m but have something decent (<150m) after 1.8s, finish.
        setTimeout(() => {
            if (!hasResolved && bestPosition && bestPosition.coords.accuracy < 150) {
                console.log("GPS: Good enough accuracy found, resolving early.");
                clearTimeout(timer);
                finish(bestPosition);
            }
        }, isAutoTriggered ? 1000 : 1800);
    });
}

function getAddressFromLatLng(lat, lng) {
    if (!googleMapsLoaded) return Promise.resolve(null);
    const geocoder = new google.maps.Geocoder();
    const latlng = { lat: parseFloat(lat), lng: parseFloat(lng) };
    return new Promise((resolve) => {
        geocoder.geocode({ location: latlng }, (results, status) => {
            if (status === "OK") {
                if (results[0]) {
                    resolve(results[0].formatted_address);
                } else {
                    resolve(null);
                }
            } else {
                console.error("Geocoder failed due to: " + status);
                resolve(null);
            }
        });
    });
}

// 3.3. Kết nối Backend (Real API Call)
async function fetchAIResponse(userMessage, userLocation) {
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: userMessage,
                latitude: userLocation ? userLocation.lat : 0.0,
                longitude: userLocation ? userLocation.lng : 0.0
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Map backend response format to frontend format
        // Backend returns: { reply: "...", nearest_experts: [ { ... }, ... ] }
        let experts = [];
        if (data.nearest_experts && data.nearest_experts.length > 0) {
            data.nearest_experts.forEach(exp => {
                experts.push({
                    name: exp.name,
                    lat: exp.lat,
                    lng: exp.lng,
                    address: exp.address,
                    expertise: exp.expertise || '',
                    distance_km: exp.distance_km,
                    zalo_link: exp.zalo_link,
                    notebook_link: exp.notebook_link || '',
                    avatar_url: exp.avatar_url || '',
                    topics: exp.topics || []
                });
            });
        }

        return {
            reply: data.reply,
            map_data: {
                user_marker: userLocation,
                expert_markers: experts
            },
            trigger_location: data.trigger_location,
            nearest_experts: experts // Direct access
        };

    } catch (error) {
        console.error("Error fetching AI response:", error);
        return {
            reply: "Xin lỗi, em không thể kết nối với máy chủ lúc này. Vui lòng thử lại sau.",
            map_data: null
        };
    }
}

// 3.4. Xử lý Chat (UI Interaction)
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-button');
const locationButton = document.getElementById('location-button');

function appendMessage(sender, text) {
    return renderMessage(sender, text, true);
}

function renderMessage(sender, text, save = true) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender);

    // Parse Markdown for AI messages, keep plain text for user
    const content = sender === 'ai' ? marked.parse(text) : text;

    messageElement.innerHTML = `<div class="message-bubble">${content}</div>`;
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight; // Auto-scroll to bottom

    // DON'T save temporary typing indicators to history
    if (save && !text.includes('typing-indicator')) {
        chatHistory.push({ type: 'message', sender, text });
        saveHistory();
    }
    return messageElement;
}

async function sendMessage() {
    const userMessage = chatInput.value.trim();
    if (userMessage === '') return;

    appendMessage('user', userMessage);
    chatInput.value = '';

    const typingIndicator = renderMessage('ai', '<div class="typing-indicator"><span></span><span></span><span></span></div>', false); // Don't save this

    // ONLY use cached location if already known; don't prompt on every message
    const location = currentUserLocation;

    const aiResponse = await fetchAIResponse(userMessage, location);

    // Remove typing indicator
    if (typingIndicator) {
        typingIndicator.remove();
    }

    if (aiResponse && !aiResponse.trigger_location) {
        appendMessage('ai', aiResponse.reply);
    }

    // Render Expert Cards
    if (aiResponse.nearest_experts && aiResponse.nearest_experts.length > 0) {
        renderExpertCards(aiResponse.nearest_experts, true);
    } else {
        // CRITICAL: Clear map if no experts found
        const lat = location ? location.lat : null;
        const lng = location ? location.lng : null;

        // Close all info windows
        if (typeof expertInfoWindows !== 'undefined') {
            expertInfoWindows.forEach(iw => iw.close());
        }

        updateMap(lat, lng, []);
    }

    // Auto-trigger location if backend requested it
    if (aiResponse.trigger_location) {
        console.log("Backend requested location trigger.");
        handleLocationCheck(true);
    }
}

function clearHistory() {
    chatHistory = [];
    localStorage.removeItem(getHistoryKey());
    sessionStorage.removeItem(getHistoryKey());
}

function renderExpertCards(experts, save = true) {
    const expertListHtml = document.createElement('div');
    expertListHtml.className = 'expert-list';

    // UPDATE CONTEXT TIMER
    window.lastSearchTime = Date.now();

    experts.forEach(expert => {
        const card = document.createElement('div');
        card.className = 'expert-card';
        card.onclick = () => focusOnExpert(expert.lat, expert.lng, expert.name);
        card.style.cursor = 'pointer';

        // Use first topic name from results
        const topicDisplay = (expert.topics && expert.topics.length > 0) ? expert.topics[0].name : "Chủ đề tri thức";

        card.innerHTML = `
            <div class="expert-header-row">
                <img src="${expert.avatar_url || '/assets/logo.png?v=3'}" class="expert-avatar" onerror="this.src='/assets/logo.png?v=3'">
                <div class="expert-header-info">
                    <div class="expert-name-header">${expert.name}</div>
                    <div class="expert-expertise">${expert.expertise || ''}</div>
                </div>
            </div>
            
            <div class="expert-distance">Cách đây: ${expert.distance_km ? expert.distance_km.toFixed(1) : '?'} km</div>
            
            ${expert.topics && expert.topics.length > 0 ? `
                <div class="topic-list">
                    ${expert.topics.map((p, index) => {
            let finalLink = p.link || '#';
            if (expert.zalo_link && finalLink !== '#') {
                const separator = finalLink.includes('?') ? '&' : '?';
                finalLink += `${separator}zalo=${encodeURIComponent(expert.zalo_link)}&topic_name=${encodeURIComponent(p.name)}`;
            } else if (finalLink !== '#') {
                const separator = finalLink.includes('?') ? '&' : '?';
                finalLink += `${separator}topic_name=${encodeURIComponent(p.name)}`;
            }

            const isHidden = index >= 2 ? 'display:none;' : ''; // Show only first 2
            const hiddenClass = index >= 2 ? 'hidden-topic' : '';

            return `
                        <div class="topic-item ${hiddenClass}" style="${isHidden}">
                            <img src="${p.image_url || '/assets/logo.png?v=3'}" class="topic-img" onerror="this.src='/assets/logo.png?v=3'">
                            <div class="topic-info">
                                <div class="topic-name-label" title="${p.name}">${p.name}</div>
                                <div class="topic-status-tag">Tri thức: ${p.status || 'Miễn phí'}</div>
                                <a href="${finalLink}" target="_self" class="topic-link-btn" onclick="event.stopPropagation()">Xem tri thức</a>
                            </div>
                        </div>`;
        }).join('')}
                    
                    ${expert.topics.length > 2 ?
                    `<button class="see-more-btn" onclick="revealNextBatch(this)">Xem thêm (${expert.topics.length - 2} chủ đề)</button>`
                    : ''}
                </div>
            ` : ''}

            <div class="expert-actions">
                ${expert.notebook_link ?
                `<a href="${expert.notebook_link}" target="_blank" class="notebook-btn" onclick="event.stopPropagation()"><i class="material-icons" style="font-size:16px;">library_books</i> Notebook</a>`
                : ''}
                ${expert.zalo_link ?
                `<a href="${expert.zalo_link}" target="_blank" class="zalo-btn-mini" onclick="trackInterest(event, '${safeEncode(expert.name)}', '${safeEncode(expert.zalo_link)}', '${safeEncode(topicDisplay)}')"><i class="material-icons" style="font-size:16px;">groups</i> Zalo Group</a>`
                : ''}
            </div>
        `;
        expertListHtml.appendChild(card);
    });
    chatMessages.appendChild(expertListHtml);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Update map markers 
    const lat = currentUserLocation ? currentUserLocation.lat : null;
    const lng = currentUserLocation ? currentUserLocation.lng : null;
    updateMap(lat, lng, experts);

    if (save) {
        chatHistory.push({ type: 'experts', data: experts });
        saveHistory();
    }
}




sendButton.addEventListener('click', sendMessage);
chatInput.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// --- 3.5. Xử lý logic lấy vị trí (Refactored - Silent UI) ---
async function handleLocationCheck(isAutoTriggered = false) {
    if (isLocating) return;

    // UI Feedback on button
    const locBtnIcon = locationButton.querySelector('i');
    if (locBtnIcon) {
        locBtnIcon.className = 'material-icons spin-icon';
        locBtnIcon.textContent = 'autorenew';
    }
    locationButton.disabled = true;

    try {
        // If manual click, clear current cached location to force a fresh scan
        if (!isAutoTriggered) {
            currentUserLocation = null;
            sessionStorage.removeItem('last_location');
        }

        const location = await getUserLocation(isAutoTriggered);

        if (location) {
            const acc = parseInt(sessionStorage.getItem('last_location_acc') || '0');
            // Get detailed address for more friendly response
            const address = await getAddressFromLatLng(location.lat, location.lng);
            let addressText = address ? ` tại **${address}**` : '';

            // If accuracy is poor, add a qualifier
            if (acc > 200) {
                addressText += " (vị trí tương đối)";
            }

            // Updated logic: ALWAYS silent for auto-trigger (as requested by user)
            // Manual click (!isAutoTriggered) still shows feedback
            if (!isAutoTriggered) {
                const prefix = acc <= 200 ? "Tuyệt vời!" : "Dạ,";
                renderMessage('ai', `${prefix} Matrix Finder AI đã nhận được vị trí của bạn${addressText}. Hãy nói cho mình biết bạn cần tìm gì nhé!`, true);
            }
            // Still mark resolved so we don't nag
            sessionStorage.setItem('locationResolved', 'true');
        } else if (!isAutoTriggered) {
            renderMessage('ai', 'Oops! 😅 Matrix Finder AI chưa thể lấy được vị trí của bạn. Bạn hãy kiểm tra lại cài đặt trình duyệt giúp mình nhé!', true);
        }
    } catch (err) {
        console.error("Location error:", err);
    } finally {
        if (locBtnIcon) {
            locBtnIcon.className = 'material-icons';
            locBtnIcon.textContent = 'my_location';
        }
        locationButton.disabled = false;
    }
}

locationButton.addEventListener('click', () => {
    renderMessage('user', 'Vị trí của tôi', true);
    handleLocationCheck(false);
});

function removeAllLoadingIndicators() {
    try {
        const indicators = document.querySelectorAll('.typing-indicator');
        indicators.forEach(ind => {
            const msg = ind.closest('.message');
            if (msg) msg.remove();
        });
    } catch (e) {
        console.error("Error cleaning indicators:", e);
    }
}

// --- Initialization & Simple Permission Logic ---
document.addEventListener('DOMContentLoaded', async () => {
    // 1. Fetch Config and Load Google Maps
    try {
        const configRes = await fetch('/api/config');
        const config = await configRes.json();

        if (config.google_maps_api_key) {
            await loadGoogleMaps(config.google_maps_api_key);
            initializeMap();

            // Try to restore cached location
            const cachedLocation = sessionStorage.getItem('last_location');
            if (cachedLocation) {
                currentUserLocation = JSON.parse(cachedLocation);
                updateMap(currentUserLocation.lat, currentUserLocation.lng, null);
            }
        }
    } catch (e) {
        console.error("Initialization error:", e);
    }

    // 2. Process parameters FIRST to determine mode
    const urlParams = new URLSearchParams(window.location.search);
    let shareId = urlParams.get('share');

    // FIX: Check for pending share params (returned from Zalo Login)
    const pendingShareParams = localStorage.getItem('pending_share_params');
    if (pendingShareParams && !shareId) {
        console.log("Found pending share params:", pendingShareParams);
        const pendingParams = new URLSearchParams(pendingShareParams);
        const pendingShareId = pendingParams.get('share');

        if (pendingShareId) {
            shareId = pendingShareId;
            // Restore URL visually
            const newUrl = window.location.pathname + pendingShareParams;
            window.history.replaceState({}, '', newUrl);
            console.log("Restored Share ID from login flow:", shareId);
        }
        localStorage.removeItem('pending_share_params');
    }

    // MODE DECISION: Shared Chat vs Normal Session
    // Robust Check: URL param > sessionStorage fallback (ONLY IF NO LOCAL HISTORY)
    const storage = getStorage();
    const savedHistory = storage.getItem(getHistoryKey());
    const shareIdFallback = sessionStorage.getItem('pending_share_id');

    if (shareIdFallback && !shareId && !savedHistory) {
        console.log("Restoring missing Share ID from fallback:", shareIdFallback);
        shareId = shareIdFallback;
        // Restore URL visually
        const newUrl = new URL(window.location);
        newUrl.searchParams.set('share', shareId);
        window.history.replaceState({}, '', newUrl);
    }

    if (shareId) {
        console.log("🚀 Mode: Shared Chat detected. ID:", shareId);
        // Shared Mode: Directly load shared content
        handleSharedChat(shareId);

        // Safety: Remove any indicators
        removeAllLoadingIndicators();
    } else {
        console.log("👤 Mode: Normal Session. Loading local history.");
        loadHistory(); // Reload local history

        // Safety: Remove any indicators
        removeAllLoadingIndicators();

        // Send welcome message (Only in Normal Mode and if no existing history)
        if (chatHistory.length === 0 && !sessionStorage.getItem('welcomeShown')) {
            setTimeout(() => {
                appendMessage('ai', 'Xin chào! Chào mừng bạn đến với <b>Matrix Finder AI</b> ✨<br>Nền tảng kết nối tri thức và chuyên gia hàng đầu. Em có thể hỗ trợ anh/chị tìm kiếm cố vấn trong lĩnh vực nào hôm nay ạ?');
                sessionStorage.setItem('welcomeShown', 'true');

                // Proactively ask for permission (Requirement 5.1 updated)
                if (!currentUserLocation) {
                    console.log("📍 Initial app load: checking location...");
                    handleLocationCheck(true);
                }
            }, 500);
        } else {
            // Already have history or welcome shown, just ensure flag is set
            sessionStorage.setItem('welcomeShown', 'true');
        }
    }




    // --- Share Button Logic ---
    const shareBtn = document.getElementById('share-btn');
    if (shareBtn) {
        shareBtn.addEventListener('click', handleShare);
    }

    const copyShareBtn = document.getElementById('copy-share-link');
    if (copyShareBtn) {
        copyShareBtn.addEventListener('click', () => {
            const input = document.getElementById('share-link-input');
            input.select();
            document.execCommand('copy');
            alert('Đã copy link chia sẻ vào bộ nhớ tạm! 📋');
        });
    }

    const forkChatBtn = document.getElementById('fork-chat-btn');
    if (forkChatBtn) {
        forkChatBtn.addEventListener('click', forkChat);
    }

    // OTHER PARAMS (Proxies, Deep links)
    const topicId = urlParams.get('topic_interest');
    const topicName = urlParams.get('topic_name');
    const zaloFromUrl = urlParams.get('zalo');
    const staffZaloFromUrl = urlParams.get('staff_zalo');

    console.log("DEBUG: Init Params - ID:", topicId, "Name:", topicName, "Zalo:", zaloFromUrl, "Staff Zalo:", staffZaloFromUrl);

    // FIX: Clean corrupted avatar from localStorage if present
    const userPic = localStorage.getItem('user_picture');
    if (userPic && (userPic === '[object Object]' || userPic.includes('object'))) {
        console.warn("Found corrupted user_picture, clearing.");
        localStorage.removeItem('user_picture');
    }
    // FIX: Clean corrupted zalo_code_verifier from localStorage if present
    const zaloCodeVerifier = localStorage.getItem('zalo_code_verifier');
    if (zaloCodeVerifier && (zaloCodeVerifier === '[object Object]' || zaloCodeVerifier.includes('object'))) {
        console.warn("Found corrupted zalo_code_verifier, clearing.");
        localStorage.removeItem('zalo_code_verifier');
    }

    if (topicId && topicName && !sessionStorage.getItem('topicProcessed_' + topicId)) {
        // Prevent re-processing on refresh
        sessionStorage.setItem('topicProcessed_' + topicId, 'true');

        const decodedName = decodeURIComponent(topicName);

        // Store in global for Lead Form to use
        window.currentTopicContext = decodedName;

        const userName = localStorage.getItem('user_name') || 'Khách';

        // Restore format: [Hệ thống ghi nhận user **Nguyễn Xuân Tài** đang quan tâm: **Tên Chủ đề**]
        const systemMessage = `[Hệ thống ghi nhận user ** ${userName} ** đang quan tâm chủ đề: ** ${decodedName} **]`;
        appendMessage('ai', systemMessage);

        // ADD TO ACCUMULATION ARRAY (when user views topic)
        window.interestedTopics.push({
            expertName: '', // Will be filled from API call below
            groupLink: zaloFromUrl || '',
            topicName: decodedName,
            timestamp: new Date().toLocaleString(),
            sent: false // Tracking flag
        });
        saveInterestedTopics();
        console.log(`✅ Added to interest list: ${decodedName} (Total: ${window.interestedTopics.length})`);

        // Note: Global function handleDualZaloAction defined at top of file

        // OPTIMIZATION: Use URL params ONLY if we have BOTH Link Group AND Link Staff
        // This prevents the "NULL" Staff ID issue if the URL is old/incomplete
        if (zaloFromUrl && zaloFromUrl.includes('http') && staffZaloFromUrl && staffZaloFromUrl.length > 5) {
            const safeLink = zaloFromUrl.trim();
            const safeStaffZalo = staffZaloFromUrl.trim();
            const topicContext = decodedName || "Chủ đề";

            const msg = encodeURIComponent(`Chào bạn, tôi quan tâm chủ đề tri thức: ${topicContext}. Nhờ hỗ trợ!`);
            const staffLink = safeStaffZalo ? `https://zalo.me/${safeStaffZalo}?text=${msg}` : "";

            let buttonsHtml = `<div>Bấm vào link bên dưới để kết nối:</div>`;

            // Button 1: Chat with Staff (REMOVED per user request)


            // Button 2: Join Group (Secondary)
            if (safeLink) {
                buttonsHtml += `<a href="${safeLink}" target="_blank" style="display: block; text-align: center; margin-top: 5px; padding: 8px 16px; background: #e0e0e0; color: #333; text-decoration: none; border-radius: 4px; font-weight: bold;">📢 Tham gia Nhóm Tri thức</a>`;
            }

            appendMessage('ai', buttonsHtml);
            return;
        }

        const statusMsg = renderMessage('ai', '<div class="typing-indicator">Đang kết nối chuyên gia...</div>', false);
        setTimeout(async () => {
            try {
                // Use standard API path
                const response = await fetch(`${window.location.origin}/api/expert-info/${topicId}`);
                const data = await response.json();
                console.log("DEBUG: Expert Info Data:", data);

                if (data && !data.error) {
                    const expertDisplay = data.expert_name || "Chuyên gia";

                    // UPDATE expert name in accumulated topics (match by topic name)
                    if (window.interestedTopics.length > 0) {
                        // Find the topic that matches this API call's topic name
                        const matchingTopic = window.interestedTopics.find(p =>
                            p.topicName === decodedName && p.expertName === ''
                        );

                        if (matchingTopic) {
                            matchingTopic.expertName = expertDisplay;
                            saveInterestedTopics();
                            console.log(`📝 Updated expert name for "${decodedName}": ${expertDisplay}`);
                        }
                    }

                    // UPDATE CONTEXT TIMER
                    window.lastSearchTime = Date.now();

                    // FIX: Strict type coercion to prevent [object Object]
                    let finalZalo = "";
                    if (data.zalo_link) {
                        if (typeof data.zalo_link === 'string') {
                            finalZalo = data.zalo_link.trim();
                        } else {
                            // Defensive: try to stringify or fallback
                            try {
                                finalZalo = String(data.zalo_link);
                                if (finalZalo === '[object Object]') finalZalo = "";
                            } catch (e) { finalZalo = ""; }
                        }
                    }

                    console.log("DEBUG: finalZalo =", finalZalo, "| Type:", typeof finalZalo);

                    // CRITICAL FIX: Build message HTML FIRST
                    let buttonsHtml = `<div>Kết nối với Chuyên gia <b>${expertDisplay}</b>:</div>`;

                    if (finalZalo) {
                        // Use Dual Action Button instead of Markdown Link
                        const safeStaff = data.staff_zalo || '';
                        const pName = data.topic_name || data.name || "Chủ đề";

                        const msg = encodeURIComponent(`Chào bạn, tôi quan tâm chủ đề tri thức: ${pName}. Nhờ hỗ trợ!`);
                        const staffLink = safeStaff ? `https://zalo.me/${safeStaff}?text=${msg}` : "";

                        // Button 1: Chat with Staff (REMOVED per user request)

                        // Button 2: Join Group
                        buttonsHtml += `<a href="${finalZalo}" target="_blank" style="display: block; text-align: center; margin-top: 5px; padding: 8px 16px; background: #e0e0e0; color: #333; text-decoration: none; border-radius: 4px; font-weight: bold;" onclick="trackInterest(event, '${safeEncode(expertDisplay)}', '${safeEncode(finalZalo)}', '${safeEncode(decodedName)}')">📢 Tham gia Nhóm Tri thức</a>`;
                    }

                    // CRITICAL: appendMessage MUST be OUTSIDE if(finalZalo) to always show message
                    appendMessage('ai', buttonsHtml);

                } else {
                    console.error("API Error or Empty Data:", data);
                    appendMessage('ai', "Không tìm thấy thông tin chuyên gia cho chủ đề này.");
                }
            } catch (err) {
                console.error("Error fetching topic info:", err);
            } finally {
                if (statusMsg) statusMsg.remove();
            }
        }, 500);

        // CLEARING URL REDIRECT removed as per user request to keep full path/params
        // window.history.replaceState({}, document.title, window.location.pathname);

        // Suppress welcome message for this mission-specific landing
        sessionStorage.setItem('welcomeShown', 'true');
    }

    console.log("Chat initialized V3.5");
});

// Reset persistence only on logout if needed (optional, keeping current localStorage behavior)
window.addEventListener('beforeunload', () => {
    // We NO LONGER clear interestedTopics here to allow navigation persistence
    // Data is stored in localStorage to survive tab closure/crashes
    console.log("💾 Maximum Persistence active: interestedTopics preserved in localStorage.");
});

// --- Helper for Topic Pagination ---
function revealNextBatch(btn) {
    const topicList = btn.parentElement;
    const hiddenItems = topicList.querySelectorAll('.topic-item.hidden-topic');

    // Convert to array to slice
    const itemsToReveal = Array.from(hiddenItems).slice(0, 3);

    itemsToReveal.forEach(item => {
        item.style.display = ''; // Reset display to default (block/flex)
        item.classList.remove('hidden-topic');
    });

    // Check remaining hidden items
    const remaining = hiddenItems.length - itemsToReveal.length;

    if (remaining > 0) {
        btn.innerText = `Xem thêm (${remaining} chủ đề)`;
    } else {
        btn.style.display = 'none'; // Hide button if no more items
    }
}

// --- LEAD GENERATION TRACKING WITH POPUP ---
let pendingLeadData = null; // Store data while waiting for phone input

// 1. Inject Modal HTML into DOM
function injectPhoneModal() {
    const modalHtml = `
    <!-- Bootstrap Modal for Phone Input -->
    <div class="modal fade" id="phoneInputModal" tabindex="-1" aria-labelledby="phoneModalLabel" aria-hidden="true" data-bs-backdrop="static" data-bs-keyboard="false">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content" style="border-radius: 16px; border: none; box-shadow: 0 10px 30px rgba(0,0,0,0.2);">
                <div class="modal-header" style="background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%); color: white; border-top-left-radius: 16px; border-top-right-radius: 16px;">
                    <h5 class="modal-title" id="phoneModalLabel">🎓 Kết nối Tri thức</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close" onclick="confirmLead('exit')"></button>
                </div>
                <div class="modal-body text-center p-4">
                    <div class="mb-3">
                        <i class="fas fa-graduation-cap fa-3x text-warning mb-3"></i>
                        <p class="fs-5 fw-bold" style="color: #333;">Để lại SĐT để được Chuyên gia hỗ trợ tốt nhất nhé!</p>
                        <p class="text-muted small">Chúng tôi sẽ kết nối bạn vào nhóm Zalo chuyên môn & Gửi tài liệu.</p>
                    </div>
                    <div class="form-floating mb-3">
                        <input type="tel" class="form-control" id="userPhoneInput" placeholder="Số điện thoại của bạn" style="border-radius: 10px;">
                        <label for="userPhoneInput">Nhập số điện thoại (Zalo)</label>
                    </div>
                </div>
                <div class="modal-footer justify-content-between border-0 pb-4">
                    <button type="button" class="btn btn-outline-secondary px-3" style="border-radius: 20px;" onclick="confirmLead('exit')">
                        ❌ Thoát
                    </button>
                    <button type="button" class="btn btn-outline-primary px-3" style="border-radius: 20px;" onclick="confirmLead('skip')">
                        ⏩ Không cần
                    </button>
                    <button type="button" class="btn btn-primary px-4 fw-bold" style="border-radius: 20px; background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%); border: none;" onclick="confirmLead('submit')">
                        Xác nhận & Kết nối 🚀
                    </button>
                </div>
            </div>
        </div>
    </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);
}

// Ensure Modal is injected on load
document.addEventListener('DOMContentLoaded', () => {
    injectPhoneModal();
});

// 2. Main Entry Point: Triggered by Button Click
function trackInterest(event, expertNameEncoded, groupLinkEncoded, topicNameEncoded) {
    if (event) event.preventDefault(); // Stop immediate navigation

    // Decode Data
    const expertName = decodeURIComponent(expertNameEncoded);
    const groupLink = decodeURIComponent(groupLinkEncoded);
    let topicName = decodeURIComponent(topicNameEncoded);

    // FIX: If topicName is generic "Chủ đề", try to find real name from array
    if (topicName === "Chủ đề" || topicName === expertName) {
        // Search from newest to oldest, prioritizing NOT SENT items
        const candidate = [...window.interestedTopics].reverse().find(p =>
            p.expertName === expertName && !p.sent
        ) || [...window.interestedTopics].reverse().find(p => p.expertName === expertName);

        if (candidate && candidate.topicName !== "Chủ đề") {
            topicName = candidate.topicName;
            console.log(`🔄 Resolved "${expertName}" -> "${topicName}" (Recent Priority)`);
        }
    }

    // ADD TO ACCUMULATION (for direct "Join Group" clicks without viewing topic detail)
    // Check if already exists
    const existingIndex = window.interestedTopics.findIndex(p =>
        p.topicName === topicName
    );

    if (existingIndex === -1) {
        // New topic
        window.interestedTopics.push({
            expertName,
            groupLink,
            topicName,
            timestamp: new Date().toLocaleString(),
            sent: false // Tracking flag
        });
        saveInterestedTopics();
        console.log(`✅ Added to interest list: ${topicName} (Total: ${window.interestedTopics.length})`);
    } else {
        const topic = window.interestedTopics[existingIndex];
        if (topic.sent) {
            // User wants to interest again - Re-activate!
            topic.sent = false;
            topic.timestamp = new Date().toLocaleString();
            saveInterestedTopics();
            console.log(`🔄 Re-activated interest for: ${topicName}`);
        } else {
            console.log(`⚠️ Topic already in queue: ${topicName}`);
        }
    }

    // Save to global for Modal callback
    pendingLeadData = {
        expertName,
        groupLink,
        topicName
    };

    // FIX 3: CHECK IF MODAL WAS ALREADY SHOWN OR PHONE EXISTS
    const storedPhone = localStorage.getItem('user_phone');
    const modalShown = localStorage.getItem('lead_modal_shown');

    if ((storedPhone && storedPhone !== "None" && storedPhone !== "null") || modalShown === 'true') {
        console.log("📱 Skipping form (Phone exists or Modal already shown once).");
        submitLeadPayload(storedPhone || "None");
        return;
    }

    // Mark as shown immediately so even if they refresh or skip, it won't show again
    localStorage.setItem('lead_modal_shown', 'true');

    // Show Modal (only if no phone stored)
    const modalEl = document.getElementById('phoneInputModal');
    if (typeof bootstrap !== 'undefined' && modalEl) {
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    } else {
        // Fallback if Bootstrap not loaded: proceed without phone
        console.warn("Bootstrap Modal not found, skipping phone input.");
        submitLeadPayload(null);
    }
}

// 3. User Decision Handler (Submit or Skip or Exit)
function confirmLead(action) {
    const modalEl = document.getElementById('phoneInputModal');
    const modal = bootstrap.Modal.getInstance(modalEl);

    // ACTION 1: Exit - Close modal and do nothing
    if (action === 'exit') {
        if (modal) modal.hide();
        console.log("❌ User exited modal");
        return;
    }

    // ACTION 2 & 3: Skip or Submit
    let phone = "None"; // Default

    if (action === 'submit') {
        const input = document.getElementById('userPhoneInput');
        if (input && input.value.trim().length > 0) {
            phone = input.value.trim();
            localStorage.setItem('user_phone', phone); // PERSIST
        } else {
            // User clicked Submit but empty? Alert
            alert("Vui lòng nhập số điện thoại hoặc chọn 'Không cần'");
            return; // Stay in modal
        }
    }

    // Hide Modal
    if (modal) modal.hide();

    // Proceed to send data
    submitLeadPayload(phone);
}

// 4. Submit Data & Navigate
async function submitLeadPayload(phone) {
    if (!pendingLeadData) return;

    const { groupLink, expertName, topicName } = pendingLeadData;

    // B. Send ALL accumulated topics as separate rows
    if (window.interestedTopics.length === 0) {
        console.warn("⚠️ No topics in interest list!");
        return;
    }

    try {
        // Collect Context (shared for all topics)
        const contextMsgs = chatHistory.filter(item => {
            return item.sender === 'user' || item.type === 'trigger';
        }).slice(-10); // Increase to 10 for better context
        const contextStr = contextMsgs.map(m => m.text).join(" - ");

        // Only send topics that haven't been submitted yet
        const unsentTopics = window.interestedTopics.filter(p => !p.sent);

        if (unsentTopics.length === 0) {
            console.log(`ℹ️ All ${window.interestedTopics.length} topics already sent previously.`);
        } else {
            console.log(`📤 Submitting ${unsentTopics.length} new topics to sheet...`);

            // Send each topic as a separate row
            for (const topic of unsentTopics) {
                const payload = {
                    user_name: localStorage.getItem('user_name') || "Khách",
                    user_id: localStorage.getItem('session_id') || "guest",
                    topic_name: topic.topicName,
                    expert_name: topic.expertName,
                    chat_context: contextStr || "Người dùng quan tâm chuyên môn",
                    phone: phone, // Actual Phone or "None"
                    zalo_contact: phone, // Backward compatibility
                    avatar_url: localStorage.getItem('user_picture') || "",
                    zalo_group_link: topic.groupLink,
                    timestamp: topic.timestamp
                };

                // Send API (fire and forget)
                fetch('/api/submit-lead', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                }).then(() => {
                    console.log(`✅ Sent: ${topic.topicName}`);
                    topic.sent = true; // Mark as sent in memory
                    saveInterestedTopics(); // Persist the 'sent' state
                }).catch(e => {
                    console.error(`❌ Failed: ${topic.topicName}`, e);
                });
            }
        }

        console.log(`✅ Submission process complete. Array preserved (Total: ${window.interestedTopics.length}).`);

        /*
        const phoneDisplay = phone && phone !== "None" ? phone : "chưa cung cấp SĐT";
        const phoneDisplay = phone && phone !== "None" ? phone : "chưa cung cấp SĐT";
        const aiMessage = `Tuyệt vời! ✨ Matrix Finder AI đã ghi nhận bạn quan tâm đến **${topicName}** cùng chuyên gia **${expertName}**.\n\n` +
            `📱 SĐT của bạn: **${phoneDisplay}**\n\n` +
            `🔗 **[Tham gia nhóm Zalo tri thức ngay!](${groupLink})**\n\n` +
            `_Nhóm sẽ tự động mở trong giây lát..._`;

        renderMessage('ai', aiMessage, true);
        */

        // B. OPEN ZALO LINK AFTER DELAY (FIX 1: Ensure message is rendered first)
        setTimeout(() => {
            window.open(groupLink, '_blank');
        }, 800); // 800ms delay to ensure message is visible

    } catch (e) {
        console.error("Tracking Error:", e);
    }

    // Reset
    pendingLeadData = null;
    const phoneInput = document.getElementById('userPhoneInput');
    if (phoneInput) phoneInput.value = ''; // Clear input
}

// --- Sharing & Forking Functions ---

async function handleShare() {
    if (chatHistory.length === 0) {
        alert("Chưa có nội dung gì để chia sẻ bạn ơi!");
        return;
    }

    const shareBtn = document.getElementById('share-btn');
    const originalContent = shareBtn.innerHTML;
    shareBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i>';
    shareBtn.disabled = true;

    try {
        const payload = {
            messages: chatHistory,
            user_info: {
                name: localStorage.getItem('user_name') || "Khách",
                avatar: localStorage.getItem('user_picture') || ""
            },
            owner_id: localStorage.getItem('session_id')
        };

        const response = await fetch('/api/share', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error("API Share failed");

        const data = await response.json();
        const shareUrl = `${window.location.origin}${window.location.pathname}?share=${data.share_id}`;

        // Show Modal
        const input = document.getElementById('share-link-input');
        input.value = shareUrl;

        const modalEl = document.getElementById('shareModal');
        const modal = new bootstrap.Modal(modalEl);
        modal.show();

    } catch (e) {
        console.error("Sharing error:", e);
        alert("Lỗi khi tạo link chia sẻ. Vui lòng thử lại sau.");
    } finally {
        shareBtn.innerHTML = originalContent;
        shareBtn.disabled = false;
    }
}
// Expose for avatar-display.js
window.handleShare = handleShare;

let sharedChatData = null;

async function handleSharedChat(shareId) {
    console.log("🔗 Loading shared chat:", shareId);

    // Show loading state in chat (DO NOT SAVE TO HISTORY)
    const loadingMsg = renderMessage('ai', '<i>Đang nạp cuộc hội thoại được chia sẻ...</i>', false);

    try {
        const response = await fetch(`/api/share/${shareId}`);
        if (!response.ok) throw new Error("Failed to load shared chat");

        const data = await response.json();
        sharedChatData = data;

        // Clear current view and history placeholder
        chatMessages.innerHTML = '';

        // Render shared messages
        const messages = data.messages || [];
        messages.forEach(item => {
            if (item.type === 'message') {
                // FIX: Auto-heal corrupted history (remove saved loading messages)
                if (item.text.includes('Đang nạp cuộc hội thoại được chia sẻ')) return;
                renderMessage(item.sender, item.text, false);
            } else if (item.type === 'stores') {
                renderStoreCards(item.data, false);
            }
        });

        // Detect Ownership
        const currentSessionId = localStorage.getItem('session_id');
        const isOwner = (data.owner_id && data.owner_id === currentSessionId);

        // Show Shared Mode Banner with original user's info
        const banner = document.getElementById('shared-mode-banner');
        const bannerText = document.getElementById('shared-banner-text');
        const forkBtn = document.getElementById('fork-chat-btn');

        const originalName = data.user_info ? data.user_info.name : 'một người dùng';
        const originalAvatar = data.user_info ? data.user_info.avatar : '';

        let avatarHtml = originalAvatar
            ? `<img src="${originalAvatar}" class="sharer-avatar" alt="Avatar">`
            : `<i class="fas fa-user-circle sharer-avatar" style="font-size: 20px; color: #17a2b8; background: white; border-radius: 50%;"></i>`;

        if (isOwner) {
            bannerText.innerHTML = `⭐ <b>Đây là đoạn chat bạn đã chia sẻ.</b>`;
            if (forkBtn) forkBtn.style.display = 'none'; // No need to fork own chat
        } else {
            bannerText.innerHTML = `Bạn đang xem đoạn chat được chia sẻ từ ${avatarHtml} <b>${originalName}</b>.`;
            if (forkBtn) forkBtn.style.display = 'inline-block';
        }

        banner.style.setProperty('display', 'flex', 'important');

        // Disable Input until "Fork"
        chatInput.disabled = true;
        sendButton.disabled = true;
        locationButton.disabled = true;
        chatInput.placeholder = "Bấm 'Chat tiếp' để tiếp tục cuộc hội thoại này";

    } catch (e) {
        console.error("Load shared chat error:", e);
        loadingMsg.innerHTML = '<div class="message-bubble text-danger">Không thể tải cuộc hội thoại này hoặc link đã hết hạn.</div>';
    }
}

function forkChat() {
    if (!sharedChatData) return;

    // Import messages into current session history
    chatHistory = [...sharedChatData.messages];
    saveHistory();

    // Enable UI
    chatInput.disabled = false;
    sendButton.disabled = false;
    locationButton.disabled = false;
    chatInput.placeholder = "Nhập tin nhắn...";

    // Hide Banner
    const banner = document.getElementById('shared-mode-banner');
    banner.style.setProperty('display', 'none', 'important');

    const originalName = sharedChatData.user_info ? sharedChatData.user_info.name : 'một người dùng';
    appendMessage('ai', `<b>✅ Đã nạp thành công!</b> Bạn có thể tiếp tục cuộc hội thoại của <b>${originalName}</b> từ đây. 🚀`);

    // Clean URL and Session Fallback
    sessionStorage.removeItem('pending_share_id');
    const url = new URL(window.location);
    url.searchParams.delete('share');
    window.history.replaceState({}, '', url);
}

function safeEncode(str) {
    if (!str) return '';
    return encodeURIComponent(str).replace(/'/g, "%27");
}
