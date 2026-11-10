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
            box-shadow: 0 8px 30px rgba(0,0,0,0.15); width: 340px;
            max-height: 90vh; overflow-y: auto;
            transition: opacity 0.5s ease;
        }
        h1 { margin: 0 0 15px 0; font-size: 22px; color: #1a1a1a; font-weight: 800; letter-spacing: -0.5px;}
        
        .input-group { margin-bottom: 12px; }
        label { display: block; font-size: 12px; color: #666; margin-bottom: 4px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;}
        input { width: 100%; padding: 10px; box-sizing: border-box; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; outline: none; transition: border 0.2s;}
        input:focus { border-color: #0055ff; }
        select { width: 100%; padding: 10px; box-sizing: border-box; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; margin-top: 4px; outline: none;}
        
        .coord-text { font-size: 11px; color: #28a745; margin-top: 4px; display: none; font-weight: 500;}
        .coord-text.error { color: #dc3545; }

        button {
            width: 100%; padding: 12px; background: #0055ff; color: white; 
            border: none; border-radius: 6px; cursor: pointer; font-size: 15px; font-weight: bold;
            margin-top: 8px; transition: background 0.2s;
        }
        button:hover { background: #0044cc; }
        button:disabled { background: #e0e0e0; color: #999; cursor: not-allowed; }

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
        
        .transport-emoji { font-size: 45px; filter: drop-shadow(0px 10px 5px rgba(0,0,0,0.5)); }
    </style>
</head>
<body>
    <div id="ui-overlay">
        <h1>🌍 Travel Studio</h1>
        
        <div class="input-group">
            <label>From:</label>
            <input type="text" id="from-input" placeholder="e.g. Sydney" onblur="validateInput('from')">
            <div id="from-coord" class="coord-text">✅ Coordinates found</div>
        </div>
        
        <div class="input-group">
            <label>To:</label>
            <input type="text" id="to-input" placeholder="e.g. Canberra" onblur="validateInput('to')">
            <div id="to-coord" class="coord-text">✅ Coordinates found</div>
        </div>

        <div class="input-group">
            <label>Transport:</label>
            <select id="transport-select">
                <option value="🚗 Car">🚗 Car</option>
                <option value="🚆 Train">🚆 Train</option>
                <option value="✈️ Plane">✈️ Plane</option>
                <option value="🚢 Ship">🚢 Ship</option>
            </select>
        </div>

        <button id="add-btn" onclick="addLeg()" disabled>+ Add Leg to Trip</button>

        <div id="trip-grid">
            <label style="margin-bottom: 10px;">Your Trip:</label>
            <div id="leg-list"></div>
        </div>

        <button id="play-btn" onclick="startAnimation()" style="display: none; background: #28a745; margin-top: 15px;">▶ Play Journey</button>
    </div>
    
    <div id="map"></div>
    
    <script>
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

        async function getCoordinates(placeName) {
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
            const input = document.getElementById(type + '-input').value;
            const coordDiv = document.getElementById(type + '-coord');
            if (!input) return;
            
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
                div.innerHTML = `
                    <div class="leg-text">${leg.transport.split(' ')[0]} ${leg.fromName} → ${leg.toName}</div>
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

        // --- THE NEW MATH FUNCTIONS ---
        function getDistanceKm(coord1, coord2) {
            const R = 6371; // Earth radius in km
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
            // Your Custom Formula
            let zoom = Math.max(1, Math.min(24, 21.43 - 1.495 * Math.log2(distanceKm)));
            
            // Dynamic Pitch based on distance
            let pitch = 0;
            if (distanceKm < 50) pitch = 55;        // Local (Street level)
            else if (distanceKm < 150) pitch = 50;  // Short regional
            else if (distanceKm < 1000) pitch = 40; // Medium regional
            else if (distanceKm < 3000) pitch = 20; // Country level
            else pitch = 0;                         // Continental / Ocean
            
            // Cap max zoom so it doesn't look pixelated
            if (zoom > 16) zoom = 16;
            
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

            document.getElementById('play-btn').style.display = 'none';
            document.getElementById('ui-overlay').style.opacity = '0.3'; 
            document.getElementById('ui-overlay').style.pointerEvents = 'none';

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
                    // Great Circle for ANY long-haul transport
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
                    // Local routing (Linear interpolation)
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
                    document.getElementById('ui-overlay').style.opacity = '1';
                    document.getElementById('ui-overlay').style.pointerEvents = 'auto';
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