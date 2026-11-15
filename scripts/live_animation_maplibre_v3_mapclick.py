import os
import webbrowser

html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Cinematic Travel App</title>
    <script src="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.js"></script>
    <link href="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.css" rel="stylesheet" />
    <style>
        body { margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        #map { position: absolute; top: 0; bottom: 0; width: 100%; }
        
        #ui-overlay {
            position: absolute; top: 20px; left: 20px; z-index: 10;
            background: rgba(255, 255, 255, 0.95); padding: 20px; border-radius: 12px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.15); width: 360px;
            max-height: 90vh; overflow-y: auto;
            transition: transform 0.3s ease, opacity 0.5s ease;
        }

        #ui-overlay.hidden { transform: translateX(-380px); }

        #toggle-btn {
            position: absolute; top: 20px; left: 380px; z-index: 11;
            width: 30px; height: 40px; background: rgba(255, 255, 255, 0.95);
            border: none; border-radius: 0 8px 8px 0; box-shadow: 4px 0 10px rgba(0,0,0,0.1);
            cursor: pointer; font-weight: bold; font-size: 16px; color: #333;
            display: flex; align-items: center; justify-content: center; transition: left 0.3s ease;
        }
        #ui-overlay.hidden + #toggle-btn { left: 0; }
        #toggle-btn:hover { background: #0055ff; color: white; }
        
        h1 { margin: 0 0 15px 0; font-size: 22px; color: #1a1a1a; font-weight: 800; letter-spacing: -0.5px;}
        
        .input-group { margin-bottom: 12px; }
        label { display: block; font-size: 12px; color: #666; margin-bottom: 4px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;}
        
        .input-row { display: flex; gap: 8px; }
        input { flex: 1; padding: 10px; box-sizing: border-box; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; outline: none; transition: border 0.2s;}
        input:focus { border-color: #0055ff; }
        
        .pick-btn {
            padding: 0 12px; background: #f0f0f0; border: 1px solid #ddd; border-radius: 6px;
            cursor: pointer; font-size: 16px; transition: all 0.2s;
            display: flex; align-items: center; justify-content: center;
        }
        .pick-btn:hover { background: #e0e0e0; }
        .pick-btn.active { background: #0055ff; color: white; border-color: #0055ff; animation: pulse 1.5s infinite; }

        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(0,85,255, 0.4); }
            70% { box-shadow: 0 0 0 10px rgba(0,85,255, 0); }
            100% { box-shadow: 0 0 0 0 rgba(0,85,255, 0); }
        }

        select { width: 100%; padding: 10px; box-sizing: border-box; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; margin-top: 4px; outline: none;}
        
        .coord-text { font-size: 11px; color: #28a745; margin-top: 4px; display: none; font-weight: 500;}
        .coord-text.error { color: #dc3545; }

        button.add-btn {
            width: 100%; padding: 12px; background: #0055ff; color: white; 
            border: none; border-radius: 6px; cursor: pointer; font-size: 15px; font-weight: bold;
            margin-top: 8px; transition: background 0.2s;
        }
        button.add-btn:hover { background: #0044cc; }
        button.add-btn:disabled { background: #e0e0e0; color: #999; cursor: not-allowed; }

        #trip-grid { margin-top: 20px; border-top: 1px solid #eee; padding-top: 15px; display: none; }
        .leg-item { 
            display: flex; justify-content: space-between; align-items: center; 
            background: #f8f9fa; padding: 10px; border-radius: 6px; margin-bottom: 8px; 
            font-size: 13px; border-left: 4px solid #0055ff;
        }
        .leg-text { flex: 1; color: #333; font-weight: 500; line-height: 1.4; margin-right: 10px;}
        .delete-btn { 
            background: #ffe5e5; color: #dc3545; border: none; border-radius: 4px; 
            width: 28px; height: 28px; cursor: pointer; font-weight: bold; 
            display: flex; align-items: center; justify-content: center;
            font-size: 14px; flex-shrink: 0;
        }
        .delete-btn:hover { background: #dc3545; color: white; }
        
        button.play-btn {
            width: 100%; padding: 12px; background: #28a745; color: white;
            border: none; border-radius: 6px; cursor: pointer; font-size: 15px; font-weight: bold;
            margin-top: 15px; transition: background 0.2s; display: none;
        }
        button.play-btn:hover { background: #218838; }

        .transport-emoji { font-size: 45px; filter: drop-shadow(0px 10px 5px rgba(0,0,0,0.5)); }
    </style>
</head>
<body>
    <div id="ui-overlay">
        <h1>🌍 Travel Studio</h1>
        
        <div class="input-group">
            <label>From:</label>
            <div class="input-row">
                <input type="text" id="from-input" placeholder="e.g. Sydney" onblur="validateInput('from')">
                <button class="pick-btn" id="pick-from-btn" onclick="togglePickMode('from')" title="Pick From Location on Map">📍</button>
            </div>
            <div id="from-coord" class="coord-text">✅ Coordinates found</div>
        </div>
        
        <div class="input-group">
            <label>To:</label>
            <div class="input-row">
                <input type="text" id="to-input" placeholder="e.g. Canberra" onblur="validateInput('to')">
                <button class="pick-btn" id="pick-to-btn" onclick="togglePickMode('to')" title="Pick To Location on Map">📍</button>
            </div>
            <div id="to-coord" class="coord-text">✅ Coordinates found</div>
        </div>

        <div class="input-group">
            <label>Transport:</label>
            <select id="transport-select">
                <optgroup label="Ground Transport">
                    <option value="🚶 Walking">🚶 Walking</option>
                    <option value="🚲 Bicycle">🚲 Bicycle</option>
                    <option value="🚗 Car">🚗 Car</option>
                    <option value="🏍️ Motorbike">🏍️ Motorbike</option>
                    <option value="🚌 Bus">🚌 Bus</option>
                    <option value="🚆 Train">🚆 Train</option>
                </optgroup>
                <optgroup label="Animals">
                    <option value="🐎 Horse">🐎 Horse</option>
                    <option value="🐪 Camel">🐪 Camel</option>
                    <option value="🫏 Donkey">🫏 Donkey</option>
                </optgroup>
                <optgroup label="Air Transport">
                    <option value="✈️ Plane">✈️ Plane</option>
                    <option value="🚁 Helicopter">🚁 Helicopter</option>
                    <option value="🛸 Drone">🛸 Drone</option>
                </optgroup>
                <optgroup label="Water Transport">
                    <option value="🚢 Ship">🚢 Ship</option>
                    <option value="⛵ Boat">⛵ Boat</option>
                    <option value="🏊 Swimming">🏊 Swimming</option>
                </optgroup>
            </select>
        </div>

        <button class="add-btn" id="add-btn" onclick="addLeg()" disabled>+ Add Leg to Trip</button>

        <div id="trip-grid">
            <label style="margin-bottom: 10px;">Your Trip:</label>
            <div id="leg-list"></div>
        </div>

        <button class="play-btn" id="play-btn" onclick="startAnimation()">▶ Play Journey</button>
    </div>
    
    <button id="toggle-btn" onclick="togglePanel()">&lt;</button>
    
    <div id="map"></div>
    
    <script>
        let panelOpen = true;
        function togglePanel() {
            const panel = document.getElementById('ui-overlay');
            const btn = document.getElementById('toggle-btn');
            panelOpen = !panelOpen;
            
            if (panelOpen) {
                panel.classList.remove('hidden');
                btn.innerHTML = '&lt;'; 
            } else {
                panel.classList.add('hidden');
                btn.innerHTML = '&gt;'; 
            }
        }

        const map = new maplibregl.Map({
            container: 'map',
            style: 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json',
            center: [151.2093, -33.8688], 
            zoom: 1, pitch: 0, bearing: 0, antialias: true
        });

        let fromCoord = null;
        let toCoord = null;
        let tripLegs = []; 
        let activeMarker = null; 
        let droppedMarkers = []; 
        let animationInterval = null;
        let tempMarkers = []; 
        
        let pickMode = null; 

        map.on('load', () => {
            map.addSource('terrain', { type: 'raster-dem', url: 'https://demotiles.maplibre.org/terrain-tiles/tiles.json', tileSize: 256 });
            map.setTerrain({ source: 'terrain', exaggeration: 1.5 });
            
            map.addSource('active-route', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
            map.addLayer({
                id: 'active-route', type: 'line', source: 'active-route',
                layout: { 'line-join': 'round', 'line-cap': 'round' },
                paint: { 'line-color': '#0055ff', 'line-width': 5 }
            });
        });

        map.on('click', (e) => {
            if (!pickMode) return; 
            
            const lng = e.lngLat.lng;
            const lat = e.lngLat.lat;
            const coordString = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
            
            if (pickMode === 'from') {
                document.getElementById('from-input').value = coordString;
                fromCoord = [lng, lat];
                document.getElementById('from-coord').innerText = `✅ Picked: ${coordString}`;
                document.getElementById('from-coord').style.display = 'block';
                document.getElementById('from-coord').className = 'coord-text';
                
                const marker = new maplibregl.Marker({color: 'green'}).setLngLat([lng, lat]).addTo(map);
                tempMarkers.push(marker);
            } else if (pickMode === 'to') {
                document.getElementById('to-input').value = coordString;
                toCoord = [lng, lat];
                document.getElementById('to-coord').innerText = `✅ Picked: ${coordString}`;
                document.getElementById('to-coord').style.display = 'block';
                document.getElementById('to-coord').className = 'coord-text';
                
                const marker = new maplibregl.Marker({color: 'red'}).setLngLat([lng, lat]).addTo(map);
                tempMarkers.push(marker);
            }
            
            // THE FIX: We do NOT call togglePickMode(null) here anymore!
            // The pin stays blue and pulsing until the user tabs out or clicks it again.
            
            document.getElementById('add-btn').disabled = !(fromCoord && toCoord);
        });

        function togglePickMode(type) {
            if (pickMode === type) type = null;
            pickMode = type;
            
            const fromBtn = document.getElementById('pick-from-btn');
            const toBtn = document.getElementById('pick-to-btn');
            
            fromBtn.classList.remove('active');
            toBtn.classList.remove('active');
            
            if (type === 'from') {
                fromBtn.classList.add('active');
                document.getElementById('from-coord').innerText = 'Click on the map to pick...';
                document.getElementById('from-coord').style.display = 'block';
            } else if (type === 'to') {
                toBtn.classList.add('active');
                document.getElementById('to-coord').innerText = 'Click on the map to pick...';
                document.getElementById('to-coord').style.display = 'block';
            }
        }

        async function getCoordinates(placeName) {
            const coordRegex = /^(-?\d+(\.\d+)?),\s*(-?\d+(\.\d+)?)$/;
            if (coordRegex.test(placeName)) {
                const parts = placeName.split(',');
                return [parseFloat(parts[1].trim()), parseFloat(parts[0].trim())]; 
            }
            
            if(!placeName) return null;
            const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(placeName)}&limit=1`;
            const response = await fetch(url, { headers: { 'User-Agent': 'TravelApp/1.0' } });
            const data = await response.json();
            if (data.length > 0) {
                return [parseFloat(data[0].lon), parseFloat(data[0].lat)];
            }
            return null;
        }

        async function validateInput(type) {
            // If the user tabs out while the pin is pressed, release it and STOP.
            if (pickMode === type) {
                togglePickMode(null);
                return; // <-- THE FIX: Exit immediately so no search is triggered
            }
            
            const input = document.getElementById(type + '-input').value;
            const coordDiv = document.getElementById(type + '-coord');
            if (!input) return;
            
            // Skip geocoding if the field already has our coordinate format
            const coordRegex = /^(-?\d+(\.\d+)?),\s*(-?\d+(\.\d+)?)$/;
            if (coordRegex.test(input)) return; 

            coordDiv.style.display = 'block';
            coordDiv.className = 'coord-text';
            coordDiv.innerText = 'Searching...';

            const coord = await getCoordinates(input);
            
            if (coord) {
                if (type === 'from') fromCoord = coord;
                else toCoord = coord;
                coordDiv.innerText = `✅ ${coord[1].toFixed(4)}, ${coord[0].toFixed(4)}`;
                
                const marker = new maplibregl.Marker({color: type === 'from' ? 'green' : 'red'}).setLngLat(coord).addTo(map);
                tempMarkers.push(marker);
            } else {
                if (type === 'from') fromCoord = null;
                else toCoord = null;
                coordDiv.className = 'coord-text error';
                coordDiv.innerText = '❌ Location not found';
            }
            document.getElementById('add-btn').disabled = !(fromCoord && toCoord);
        }

        function addLeg() {
            if (!fromCoord || !toCoord) return;

            const fromName = document.getElementById('from-input').value;
            const toName = document.getElementById('to-input').value;
            const transport = document.getElementById('transport-select').value;

            tripLegs.push({
                fromName: fromName, toName: toName,
                fromCoord: fromCoord, toCoord: toCoord,
                transport: transport
            });

            document.getElementById('from-input').value = toName;
            fromCoord = toCoord;
            document.getElementById('from-coord').innerText = `✅ ${fromCoord[1].toFixed(4)}, ${fromCoord[0].toFixed(4)}`;
            
            document.getElementById('to-input').value = '';
            document.getElementById('to-coord').style.display = 'none';
            toCoord = null;
            
            togglePickMode(null); 

            renderTripGrid();
        }

        function renderTripGrid() {
            const grid = document.getElementById('trip-grid');
            const list = document.getElementById('leg-list');
            
            grid.style.display = tripLegs.length > 0 ? 'block' : 'none';
            list.innerHTML = '';
            
            tripLegs.forEach((leg, index) => {
                const div = document.createElement('div');
                div.className = 'leg-item';
                
                let fromLabel = leg.fromName;
                let toLabel = leg.toName;
                if (fromLabel.includes(',')) fromLabel = '📍 Picked';
                if (toLabel.includes(',')) toLabel = '📍 Picked';

                div.innerHTML = `
                    <div class="leg-text">${leg.transport.split(' ')[0]} ${fromLabel} → ${toLabel}</div>
                    <button class="delete-btn" onclick="removeLeg(${index})">✖</button>
                `;
                list.appendChild(div);
            });

            document.getElementById('play-btn').style.display = tripLegs.length > 0 ? 'block' : 'none';
            document.getElementById('add-btn').disabled = true;
        }

        function removeLeg(index) {
            tripLegs.splice(index, 1);
            renderTripGrid();
        }

        function getDistanceKm(coord1, coord2) {
            const R = 6371; 
            const lat1 = coord1[1] * Math.PI / 180;
            const lat2 = coord2[1] * Math.PI / 180;
            let deltaLon = coord2[0] - coord1[0];
            while (deltaLon > 180) deltaLon -= 360;
            while (deltaLon < -180) deltaLon += 360;
            const deltaLonRad = deltaLon * Math.PI / 180;

            const a = Math.pow(Math.sin((lat2 - lat1) / 2), 2) + 
                      Math.cos(lat1) * Math.cos(lat2) * Math.pow(Math.sin(deltaLonRad / 2), 2);
            return 2 * R * Math.asin(Math.sqrt(a));
        }

        function getCameraSettings(distanceKm) {
            const safeDist = Math.max(0.1, distanceKm); 
            let zoom = 21.43 - 1.495 * Math.log2(safeDist);
            zoom = Math.max(2, Math.min(16, zoom)); 
            
            let pitch = 0;
            if (distanceKm < 50) pitch = 55;        
            else if (distanceKm < 150) pitch = 50;  
            else if (distanceKm < 1000) pitch = 40; 
            else if (distanceKm < 3000) pitch = 20; 
            else pitch = 0;                         
            
            return { zoom, pitch };
        }

        function startAnimation() {
            if (tripLegs.length === 0) return;
            
            if (animationInterval) clearInterval(animationInterval);
            
            tempMarkers.forEach(marker => marker.remove());
            tempMarkers = []; 

            droppedMarkers.forEach(marker => marker.remove());
            droppedMarkers = [];

            if (activeMarker) {
                activeMarker.remove();
                activeMarker = null;
            }

            map.getSource('active-route').setData({
                type: 'FeatureCollection',
                features: []
            });

            if (panelOpen) togglePanel();

            document.getElementById('play-btn').style.display = 'none';
            
            const frames = [];
            const STEPS = 100; 

            tripLegs.forEach((leg, legIndex) => {
                const transport = leg.transport;
                const startLon = leg.fromCoord[0], startLat = leg.fromCoord[1];
                const endLon = leg.toCoord[0], endLat = leg.toCoord[1];
                const icon = transport.split(' ')[0];

                const distanceKm = getDistanceKm(leg.fromCoord, leg.toCoord);
                const cam = getCameraSettings(distanceKm);
                
                let deltaLon = endLon - startLon;
                while (deltaLon > 180) deltaLon -= 360;
                while (deltaLon < -180) deltaLon += 360;
                const isLongHaul = Math.abs(deltaLon) > 20; 

                if (isLongHaul) {
                    const lat1 = startLat * Math.PI / 180, lon1 = startLon * Math.PI / 180;
                    const lat2 = endLat * Math.PI / 180, lon2 = endLon * Math.PI / 180;
                    const d = 2 * Math.asin(Math.sqrt(Math.pow(Math.sin((lat2 - lat1) / 2), 2) + Math.cos(lat1) * Math.cos(lat2) * Math.pow(Math.sin((deltaLon * Math.PI / 180) / 2), 2)));

                    for (let i = 0; i <= STEPS; i++) {
                        const f = i / STEPS;
                        const A = Math.sin((1 - f) * d) / Math.sin(d);
                        const B = Math.sin(f * d) / Math.sin(d);
                        const x = A * Math.cos(lat1) * Math.cos(lon1) + B * Math.cos(lat2) * Math.cos(lon2);
                        const y = A * Math.cos(lat1) * Math.sin(lon1) + B * Math.cos(lat2) * Math.sin(lon2);
                        const z = A * Math.sin(lat1) + B * Math.sin(lat2);
                        const lat = Math.atan2(z, Math.sqrt(x * x + y * y)) * 180 / Math.PI;
                        let lon = Math.atan2(y, x) * 180 / Math.PI;
                        while (lon > 180) lon -= 360;
                        while (lon < -180) lon += 360;
                        
                        frames.push({ 
                            lat: lat, lon: lon, icon: icon, zoom: cam.zoom, pitch: cam.pitch,
                            isLegStart: (i === 0), legIndex: legIndex
                        });
                    }
                } else {
                    for (let i = 0; i <= STEPS; i++) {
                        const f = i / STEPS;
                        frames.push({
                            lat: startLat + f * (endLat - startLat),
                            lon: startLon + f * (endLon - startLon),
                            icon: icon,
                            zoom: cam.zoom,
                            pitch: cam.pitch,
                            isLegStart: (i === 0), legIndex: legIndex
                        });
                    }
                }
            });

            const openingFrames = 60; 
            const startCoord = tripLegs[0].fromCoord;
            const firstLegDist = getDistanceKm(tripLegs[0].fromCoord, tripLegs[0].toCoord);
            const firstCam = getCameraSettings(firstLegDist);

            for (let i = 0; i <= openingFrames; i++) {
                const p = i / openingFrames;
                const smoothP = p * p * (3 - 2 * p); 
                frames.unshift({
                    lat: startCoord[1], lon: startCoord[0], icon: tripLegs[0].transport.split(' ')[0],
                    zoom: 1 + smoothP * (firstCam.zoom - 1), 
                    pitch: smoothP * firstCam.pitch,
                    isOpening: true
                });
            }

            let currentFrame = 0;
            let segments = [[]]; 
            let activeEl = null; 

            animationInterval = setInterval(() => {
                if (currentFrame >= frames.length) {
                    clearInterval(animationInterval);
                    document.getElementById('play-btn').style.display = 'block';
                    document.getElementById('play-btn').innerText = "↺ Replay Journey";
                    return;
                }

                const frame = frames[currentFrame];
                
                if (!frame.isOpening) {
                    if (frame.isLegStart) {
                        if (activeMarker) {
                            droppedMarkers.push(activeMarker);
                        }
                        
                        const newEl = document.createElement('div');
                        newEl.className = 'transport-emoji';
                        newEl.innerText = frame.icon;
                        activeMarker = new maplibregl.Marker({ element: newEl, anchor: 'center' }).setLngLat([frame.lon, frame.lat]).addTo(map);
                        activeEl = newEl;

                        segments.push([[frame.lon, frame.lat]]);
                    }
                    
                    if (activeMarker) {
                        activeMarker.setLngLat([frame.lon, frame.lat]);
                        if (activeEl) activeEl.innerText = frame.icon;
                    }

                    const currentSegment = segments[segments.length - 1];
                    const lastCoord = currentSegment[currentSegment.length - 1];
                    const newCoord = [frame.lon, frame.lat];

                    if (lastCoord && Math.abs(newCoord[0] - lastCoord[0]) > 180) {
                        segments.push([newCoord]);
                    } else {
                        currentSegment.push(newCoord);
                    }

                    map.getSource('active-route').setData({
                        type: 'FeatureCollection',
                        features: segments.map(seg => ({
                            type: 'Feature',
                            geometry: { type: 'LineString', coordinates: seg }
                        }))
                    });

                } else {
                    if (!activeMarker) {
                        const el = document.createElement('div');
                        el.className = 'transport-emoji';
                        el.innerText = frame.icon;
                        el.style.display = 'none';
                        activeMarker = new maplibregl.Marker({ element: el, anchor: 'center' }).setLngLat([frame.lon, frame.lat]).addTo(map);
                        activeEl = el;
                    }
                }

                map.jumpTo({
                    center: [frame.lon, frame.lat],
                    pitch: frame.pitch,
                    zoom: frame.zoom,
                    bearing: 0
                });

                currentFrame++;
            }, 40); 
        }
    </script>
</body>
</html>
"""

output_file = "travel_studio.html"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Success! Generated {output_file}")
webbrowser.open("file://" + os.path.abspath(output_file))