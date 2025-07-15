let lockedIndex = null;
let hoverIndex = null; // <-- Track hovered index

document.addEventListener("DOMContentLoaded", function() {
    // Map rendering
    if (window.activity.map && window.activity.map.summary_polyline) {
        var map = L.map('map');
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 18 }).addTo(map);
        var poly = polyline.decode(window.activity.map.summary_polyline);
        var latlngs = poly.map(function(coord) { return [coord[0], coord[1]]; });
        var polylineLayer = L.polyline(latlngs, {color: 'blue'}).addTo(map);
        // Add green marker at start
        if (latlngs.length > 0) {
            L.circleMarker(latlngs[0], {radius: 6, color: 'green', fillColor: 'green', fillOpacity: 1}).addTo(map);
        }
        // Add red marker at end
        if (latlngs.length > 1) {
            L.circleMarker(latlngs[latlngs.length - 1], {radius: 6, color: 'red', fillColor: 'red', fillOpacity: 1}).addTo(map);
        }
        map.fitBounds(polylineLayer.getBounds());
    } else {
        document.getElementById('map').innerHTML = "<div style='text-align:center;padding-top:100px;color:#888;'>No map available</div>";
    }

    // Lap Chart
    const laps = window.laps;
    const lapLabels = laps.map((lap, i) => `Lap ${i+1}`);
    const lapDistances = laps.map(lap => (lap.distance / 1609.34).toFixed(2));
    const lapPaces = laps.map(lap => {
        if (lap.moving_time && lap.distance) {
            const paceSec = Math.floor(lap.moving_time / (lap.distance / 1609.34));
            return paceSec ? paceSec / 60 : null;
        }
        return null;
    });
    const lapAvgHR = laps.map(lap => lap.average_heartrate || null);
    const lapAvgCadence = laps.map(lap => lap.average_cadence ? lap.average_cadence * 2 : null);
    const lapElevGain = laps.map(lap => (
        lap.total_elevation_gain !== undefined && lap.total_elevation_gain !== null
            ? lap.total_elevation_gain * 3.28084
            : null
    ));

    const ctxLap = document.getElementById('lapChart').getContext('2d');
    new Chart(ctxLap, {
        type: 'line',
        data: {
            labels: lapLabels,
            datasets: [
                {
                    label: 'Pace (min/mi)',
                    data: lapPaces,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    yAxisID: 'y1',
                    tension: 0.3,
                    spanGaps: true
                },
                {
                    label: 'Avg HR',
                    data: lapAvgHR,
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    yAxisID: 'y2',
                    tension: 0.3,
                    spanGaps: true
                },
                {
                    label: 'Avg Cadence',
                    data: lapAvgCadence,
                    borderColor: 'rgba(255, 206, 86, 1)',
                    backgroundColor: 'rgba(255, 206, 86, 0.1)',
                    yAxisID: 'y3',
                    tension: 0.3,
                    spanGaps: true
                },
                {
                    label: 'Elevation Gain (ft)',
                    data: lapElevGain,
                    borderColor: 'rgba(120,120,120,0.7)',
                    backgroundColor: 'rgba(120,120,120,0.1)',
                    yAxisID: 'y5',
                    tension: 0.3,
                    spanGaps: true,
                    fill: false,
                    order: 1
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            if (context.dataset.label === 'Pace (min/mi)' && context.parsed.y) {
                                const min = Math.floor(context.parsed.y);
                                const sec = Math.round((context.parsed.y - min) * 60);
                                return `Pace: ${min}:${sec < 10 ? '0' : ''}${sec} min/mi`;
                            }
                            if (context.dataset.label === 'Elevation Gain (ft)') {
                                return `Elevation Gain: ${Math.round(context.parsed.y)} ft`;
                            }
                            return `${context.dataset.label}: ${context.parsed.y}`;
                        }
                    }
                }
            },
            scales: {
                y1: { type: 'linear', position: 'left', title: { display: true, text: 'Pace (min/mi)' }, beginAtZero: false, reverse: true },
                y2: { type: 'linear', position: 'right', title: { display: true, text: 'Avg HR' }, beginAtZero: true, grid: { drawOnChartArea: false } },
                y3: { type: 'linear', position: 'right', title: { display: true, text: 'Avg Cadence' }, beginAtZero: true, grid: { drawOnChartArea: false }, offset: true },
                y5: { type: 'linear', position: 'right', title: { display: true, text: 'Elevation Gain (ft)' }, beginAtZero: false, grid: { drawOnChartArea: false }, offset: true }
            }
        }});

    // Full Chart
    const streams = window.streams;
    const altitudes = streams.altitude.data;
    const distances = streams.distance.data.map(d => d / 1609.34);
    const times = streams.time.data;

    const paces = [];
    for (let i = 1; i < times.length; i++) {
        const dt = times[i] - times[i-1];
        const dd = distances[i] - distances[i-1];
        if (dd > 0) {
            const pace = (dt / 60) / dd;
            paces.push(pace);
        } else {
            paces.push(null);
        }
    }
    paces.unshift(paces[0]);

    function movingAverage(arr, windowSize) {
        if (!arr || arr.length === 0 || windowSize <= 0) {
            return [];
        }

        const smoothedValues = [];
        for (let i = 0; i < arr.length; i++) {
            let start = Math.max(0, i - windowSize / 2);
            let end = Math.min(arr.length, i + windowSize / 2);
            let window = arr.slice(start, end).filter(x => x !== null);
            let outlierThreshold = calculateStandardDeviation(window) * 3; // Use 2 standard deviations as threshold

            if (window.length > 0) {
                let validSum = 0;
                for (let j = 0; j < window.length; j++) {
                    if (Math.abs(window[j] - window[j - 1]) <= outlierThreshold) {
                        validSum += window[j];
                    }
                }

                if (validSum > 0) {
                    smoothedValues.push(validSum / window.length);
                } else {
                    smoothedValues.push(null);
                }
            } else {
                smoothedValues.push(null);
            }
        }
        return smoothedValues;
    }


    // --- Crosshair plugin (unchanged) ---
    const crosshairPlugin = {
        id: 'crosshair',
        afterDraw: (chart) => {
            let index = lockedIndex !== null ? lockedIndex : hoverIndex;
            if (index !== null && chart.getDatasetMeta(0).data[index]) {
                const point = chart.getDatasetMeta(0).data[index];
                const ctx = chart.ctx;
                ctx.save();
                ctx.beginPath();
                ctx.moveTo(point.x, chart.chartArea.top);
                ctx.lineTo(point.x, chart.chartArea.bottom);
                ctx.lineWidth = 1;
                ctx.strokeStyle = '#333';
                ctx.stroke();
                ctx.restore();
            }
        }
    };
    
    // Use a window size of 10 for smoothing
    const smoothedPaces = movingAverage(paces, 10);
    const paceData = distances.map((d, i) => ({x: d, y: smoothedPaces[i]}));
    Chart.register(crosshairPlugin);
    const elevationData = distances.map((d, i) => ({x: d, y: altitudes[i] * 3.28084}));
    const ctxFull = document.getElementById('fullChart').getContext('2d');

    function calculateStandardDeviation(data) {
        const n = data.length;
        if (n === 0) return 0;
        const mean = data.reduce((sum, x) => sum + x, 0) / n;
        const sumOfSquaredDifferences = data.map(x => (x - mean) ** 2).reduce((sum, x) => sum + x, 0);
        return Math.sqrt(sumOfSquaredDifferences / (n - 1));
    }

    //Example Usage:
    const stdDev = calculateStandardDeviation(paces);
    console.log("Standard Deviation:", stdDev); // Will output a value, likely around 0.74
    // --- Custom tooltip positioner for locking ---
    const lockedTooltipPlugin = {
        id: 'lockedTooltip',
        beforeEvent(chart, args) {
            const tooltip = chart.tooltip;
            if (lockedIndex !== null) {
                // Force tooltip to show at locked index for all datasets
                const activeElements = chart.data.datasets.map((ds, i) => ({
                    datasetIndex: i,
                    index: lockedIndex
                }));
                tooltip.setActiveElements(
                    activeElements,
                    {x: chart.scales.x.getPixelForValue(distances[lockedIndex]), y: 0}
                );
                // This is the key: keep tooltip active
                tooltip._active = activeElements.map(ae => chart.getDatasetMeta(ae.datasetIndex).data[ae.index]);
                tooltip.update();
            } else if (tooltip._active && tooltip._active.length && hoverIndex === null) {
                // If not locked and not hovering, hide tooltip
                tooltip._active = [];
                tooltip.update();
            }
        }
    };
    Chart.register(lockedTooltipPlugin);

    // --- Chart creation ---
    const chart = new Chart(ctxFull, {
        type: 'line',
        data: {
            datasets: [
                {
                    label: 'Elevation (ft)',
                    data: elevationData,
                    borderColor: 'rgba(120,120,120,0.7)',
                    backgroundColor: 'rgba(120,120,120,0.1)',
                    yAxisID: 'y1',
                    pointRadius: 0,
                    tension: 0.1
                },
                {
                    label: 'Pace (min/mi)',
                    data: paceData,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    yAxisID: 'y2',
                    pointRadius: 0,
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                crosshair: {},
                tooltip: {
                    enabled: true, // <-- Always true!
                    position: 'nearest',
                    callbacks: {
                        title: function(context) {
                            const idx = context[0].dataIndex;
                            const time = times[idx];
                            const mins = Math.floor(time / 60);
                            const secs = time % 60;
                            const dist = distances[idx].toFixed(2);
                            return `Time: ${mins}:${secs < 10 ? '0' : ''}${secs} | Distance: ${dist} mi`;
                        },
                        label: function(context) {
                            if (context.dataset.label === 'Pace (min/mi)') {
                                const pace = context.parsed.y;
                                if (!pace) return 'Pace: N/A';
                                const min = Math.floor(pace);
                                const sec = Math.round((pace - min) * 60);
                                return `Pace: ${min}:${sec < 10 ? '0' : ''}${sec}/mi`;
                            }
                            if (context.dataset.label === 'Elevation (ft)') {
                                return `Elevation: ${Math.round(context.parsed.y)} ft`;
                            }
                            return `${context.dataset.label}: ${context.parsed.y}`;
                        },
                        labelColor: function(context) {
                            if (context.dataset.label === 'Elevation (ft)') {
                                return {borderColor: 'rgba(120,120,120,1)', backgroundColor: 'rgba(120,120,120,0.7)'};
                            }
                            if (context.dataset.label === 'Pace (min/mi)') {
                                return {borderColor: 'rgba(54, 162, 235, 1)', backgroundColor: 'rgba(54, 162, 235, 0.7)'};
                            }
                            return Chart.defaults.plugins.tooltip.labelColor(context);
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    title: { display: true, text: 'Distance (mi)' },
                    min: 0,
                    max: Math.ceil(distances[distances.length - 1] * 100) / 100 // Truncate to actual max distance, rounded up to 2 decimals
                },
                y1: {
                    type: 'linear',
                    position: 'left',
                    title: { display: true, text: 'Elevation (ft)' },
                    beginAtZero: false
                },
                y2: {
                    type: 'linear',
                    position: 'right',
                    title: { display: true, text: 'Pace (min/mi)' },
                    beginAtZero: false,
                    grid: { drawOnChartArea: false },
                    reverse: true
                }
            }
        }
    });

    // --- Crosshair mouse events (optimized) ---
    ctxFull.canvas.addEventListener('mousemove', function(event) {
        if (lockedIndex !== null) return;
        const points = chart.getElementsAtEventForMode(event, 'index', { intersect: false }, false);
        const newIndex = points.length ? points[0].index : null;
        if (hoverIndex !== newIndex) {
            hoverIndex = newIndex;
            chart.update('none');
        }
    });

    ctxFull.canvas.addEventListener('mouseleave', function() {
        if (lockedIndex === null && hoverIndex !== null) {
            hoverIndex = null;
            chart.update('none');
        }
    });

    ctxFull.canvas.addEventListener('click', function(event) {
        if (lockedIndex === null) {
            const points = chart.getElementsAtEventForMode(event, 'index', { intersect: false }, false);
            if (points.length) {
                lockedIndex = points[0].index;
                chart.update('none');
            }
        } else {
            lockedIndex = null;
            chart.update('none');
        }
    });
});