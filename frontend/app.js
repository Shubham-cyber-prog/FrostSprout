/**
 * FrostSprout Frontend Application Logic
 * Theme: 'Touch Grass' - Screen in Pocket, Hands in the Dirt.
 * Connects tabular frost modeling, Google Gemma action planning,
 * Web Speech API hands-free audio walkthrough, and Proof of Dirt journaling.
 */

// API Configuration (defaults to same-origin or localhost:8000)
const API_BASE = window.location.origin.includes(':') && !window.location.origin.includes(':8000') 
  ? 'http://localhost:8000' 
  : '';

// App State
const state = {
  selectedCropIds: ['garlic-hardneck', 'kale-lacinato'],
  allCrops: [],
  currentPrediction: null,
  currentPlan: null,
  activeFilter: 'all',
  isPlayingAudio: false,
  speechSynthUtterance: null,
  journalEntries: [],
  weatherMode: 'simulated',
  lastLiveWeather: null,
  currentLatitude: 29.39,
  currentLongitude: 76.97
};

// Preset Microclimate Profiles
const PRESETS = {
  'zone-6a': { minTemp: 3.5, maxTemp: 13.0, soilTemp: 8.0, cloud: 20, elev: 220, humidity: 65, doy: 284 },
  'zone-4b': { minTemp: -1.5, maxTemp: 8.0, soilTemp: 4.0, cloud: 10, elev: 450, humidity: 55, doy: 275 },
  'zone-5b': { minTemp: 1.0, maxTemp: 10.5, soilTemp: 6.5, cloud: 15, elev: 340, humidity: 60, doy: 280 },
  'zone-7b': { minTemp: 7.0, maxTemp: 18.0, soilTemp: 12.0, cloud: 45, elev: 45, humidity: 75, doy: 295 },
  'zone-8b': { minTemp: 9.0, maxTemp: 16.0, soilTemp: 13.5, cloud: 70, elev: 60, humidity: 85, doy: 310 }
};

// Fallback Default Crops Data (if offline / backend loading)
const FALLBACK_CROPS = [
  {
    id: "garlic-hardneck",
    name: "Hardneck Garlic",
    scientific: "Allium sativum var. ophioscorodon",
    category: "Alliums",
    min_soil_temp_c: 4,
    frost_tolerance: "Hardy (-20°C with mulch)",
    planting_depth_cm: 5.0,
    knuckles: "2 Knuckles Deep (5cm)",
    outdoor_action: "Plant individual cloves pointed end up, 5cm deep. Cover with 10cm straw mulch.",
    touch_grass_tip: "Soil should feel cool and damp like a wrung-out sponge, not soaked."
  },
  {
    id: "kale-lacinato",
    name: "Lacinato 'Dino' Kale",
    scientific: "Brassica oleracea var. acephala",
    category: "Brassicas",
    min_soil_temp_c: 5,
    frost_tolerance: "Hardy (-10°C, sweeter after frost)",
    planting_depth_cm: 1.2,
    knuckles: "Half Knuckle (1.2cm)",
    outdoor_action: "Direct sow seeds or transplant. Cold weather converts starches to natural plant sugars.",
    touch_grass_tip: "Taste a leaf right after a light morning frost: notice the sudden sweet flavor!"
  },
  {
    id: "spinach-bloomsdale",
    name: "Bloomsdale Long Standing Spinach",
    scientific: "Spinacia oleracea",
    category: "Greens",
    min_soil_temp_c: 2,
    frost_tolerance: "Very Hardy (-12°C)",
    planting_depth_cm: 1.5,
    knuckles: "1 Knuckle Deep (1.5cm)",
    outdoor_action: "Sow in shallow rows. Firm soil firmly with your palm for tight seed contact.",
    touch_grass_tip: "Spinach loves cold earth. Roots sleep under snow and shoot up first thing in spring."
  },
  {
    id: "carrots-nantes",
    name: "Scarlet Nantes Fall Carrot",
    scientific: "Daucus carota subsp. sativus",
    category: "Root Vegetables",
    min_soil_temp_c: 7,
    frost_tolerance: "Hardy (-6°C in ground)",
    planting_depth_cm: 0.6,
    knuckles: "Shallow Dusting (0.6cm)",
    outdoor_action: "Scatter tiny seeds in damp furrows. Top with 20cm fallen leaves for all-winter harvesting.",
    touch_grass_tip: "Dig sweet carrots straight out of half-frozen soil in mid-December."
  },
  {
    id: "arugula-wild",
    name: "Rustic Wild Arugula",
    scientific: "Diplotaxis tenuifolia",
    category: "Greens",
    min_soil_temp_c: 4,
    frost_tolerance: "Hardy (-7°C)",
    planting_depth_cm: 0.5,
    knuckles: "Surface Sprinkle (0.5cm)",
    outdoor_action: "Broadcast lightly over freshly raked soil. Lightly mist with water.",
    touch_grass_tip: "Crush a freshly picked sprig between your fingers outdoors for intense peppery aroma."
  },
  {
    id: "radish-french-breakfast",
    name: "French Breakfast Radish",
    scientific: "Raphanus sativus",
    category: "Root Vegetables",
    min_soil_temp_c: 5,
    frost_tolerance: "Semi-hardy (-4°C)",
    planting_depth_cm: 1.0,
    knuckles: "Half Knuckle (1cm)",
    outdoor_action: "Super fast 25-day crop. Poke pinky finger 1cm deep and drop seeds.",
    touch_grass_tip: "Pull crisp roots with bare hands, rinse off dirt with the cold garden hose, and take a bite!"
  },
  {
    id: "shallots-french",
    name: "French Red Shallots",
    scientific: "Allium cepa var. aggregatum",
    category: "Alliums",
    min_soil_temp_c: 4,
    frost_tolerance: "Hardy (-15°C)",
    planting_depth_cm: 3.0,
    knuckles: "1.5 Knuckles Deep (3cm)",
    outdoor_action: "Set bulb tips just kissing the soil surface. Mulch lightly with dry autumn leaves.",
    touch_grass_tip: "One single bulb planted today multiplies into 6-8 gourmet shallots by summer."
  },
  {
    id: "broad-beans-fava",
    name: "Aquadulce Claudia Fava Beans",
    scientific: "Vicia faba",
    category: "Legumes",
    min_soil_temp_c: 3,
    frost_tolerance: "Very Hardy (-10°C)",
    planting_depth_cm: 5.0,
    knuckles: "2 Knuckles Deep (5cm)",
    outdoor_action: "Plant in double rows 5cm deep. Fixes atmospheric nitrogen to feed your spring soil.",
    touch_grass_tip: "Fava roots penetrate dense winter clay, opening channels for spring earthworms."
  }
];

// DOM Elements
const elements = {
  zonePresetSelect: document.getElementById('zonePresetSelect'),
  minTempSlider: document.getElementById('minTempSlider'),
  minTempVal: document.getElementById('minTempVal'),
  soilTempSlider: document.getElementById('soilTempSlider'),
  soilTempVal: document.getElementById('soilTempVal'),
  cloudSlider: document.getElementById('cloudSlider'),
  cloudVal: document.getElementById('cloudVal'),
  elevSlider: document.getElementById('elevSlider'),
  elevVal: document.getElementById('elevVal'),
  humiditySlider: document.getElementById('humiditySlider'),
  humidityVal: document.getElementById('humidityVal'),
  doySlider: document.getElementById('doySlider'),
  doyVal: document.getElementById('doyVal'),
  btnRunPrediction: document.getElementById('btnRunPrediction'),

  // Live Weather Telemetry Elements
  btnLiveWeatherPanipat: document.getElementById('btnLiveWeatherPanipat'),
  weatherModeBadge: document.getElementById('weatherModeBadge'),
  weatherLocationText: document.getElementById('weatherLocationText'),
  weatherFetchTimeText: document.getElementById('weatherFetchTimeText'),
  defaultedNoticeBadge: document.getElementById('defaultedNoticeBadge'),
  liveWeatherDetails: document.getElementById('liveWeatherDetails'),
  liveTelemetryBreakdown: document.getElementById('liveTelemetryBreakdown'),
  liveWeatherErrorBox: document.getElementById('liveWeatherErrorBox'),
  liveWeatherErrorText: document.getElementById('liveWeatherErrorText'),
  
  // Radar & Hero Elements
  gaugeBar: document.getElementById('gaugeBar'),
  frostProbPercent: document.getElementById('frostProbPercent'),
  threatLevelText: document.getElementById('threatLevelText'),
  daysToFrostText: document.getElementById('daysToFrostText'),
  radiativeAnomalyText: document.getElementById('radiativeAnomalyText'),
  frostActionSummaryText: document.getElementById('frostActionSummaryText'),
  heroStreakDisplay: document.getElementById('heroStreakDisplay'),
  heroDaysDisplay: document.getElementById('heroDaysDisplay'),
  heroStatusDisplay: document.getElementById('heroStatusDisplay'),
  modelBadge: document.getElementById('modelBadge'),
  headerModelBadge: document.getElementById('headerModelBadge'),
  
  // Crops Grid & Actions
  cropsGrid: document.getElementById('cropsGrid'),
  categoryFilterTabs: document.getElementById('categoryFilterTabs'),
  selectedCountDisplay: document.getElementById('selectedCountDisplay'),
  btnGeneratePlan: document.getElementById('btnGeneratePlan'),
  
  // Outdoor Plan Elements
  choresList: document.getElementById('choresList'),
  sensoryBoxText: document.getElementById('sensoryBoxText'),
  synergyContentText: document.getElementById('synergyContentText'),
  btnPrintPocketCard: document.getElementById('btnPrintPocketCard'),
  btnLogOutdoorSession: document.getElementById('btnLogOutdoorSession'),
  
  // Audio Elements
  btnAudioPlay: document.getElementById('btnAudioPlay'),
  audioPlayIcon: document.getElementById('audioPlayIcon'),
  audioTrackTitle: document.getElementById('audioTrackTitle'),
  audioWaveform: document.getElementById('audioWaveform'),
  btnQuickAudioWalk: document.getElementById('btnQuickAudioWalk'),
  
  // Journal Form & History
  journalForm: document.getElementById('journalForm'),
  journalMinutesInput: document.getElementById('journalMinutesInput'),
  journalSoilFeelSelect: document.getElementById('journalSoilFeelSelect'),
  journalNotesInput: document.getElementById('journalNotesInput'),
  journalHistoryList: document.getElementById('journalHistoryList'),
  streakBadgeText: document.getElementById('streakBadgeText'),
  
  // Modals
  benchmarkModal: document.getElementById('benchmarkModal'),
  benchmarkModalBody: document.getElementById('benchmarkModalBody'),
  btnOpenBenchmark: document.getElementById('btnOpenBenchmark'),
  btnCloseBenchmark: document.getElementById('btnCloseBenchmark'),
  
  // Print Template
  printCardDate: document.getElementById('printCardDate'),
  printWeatherBar: document.getElementById('printWeatherBar'),
  printCropsSection: document.getElementById('printCropsSection'),
  printChoresSection: document.getElementById('printChoresSection')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  loadInitialData();
});

// Setup Event Listeners
function setupEventListeners() {
  // Preset selector
  elements.zonePresetSelect.addEventListener('change', (e) => {
    const val = e.target.value;
    if (PRESETS[val]) {
      state.weatherMode = 'what-if';
      if (elements.weatherModeBadge) {
        elements.weatherModeBadge.textContent = 'Mode: Preset (Simulated)';
        elements.weatherModeBadge.className = 'badge badge-warn';
      }
      applyPreset(PRESETS[val]);
      runPrediction();
    }
  });

  // What-if mode helper for manual slider adjustments
  function markWhatIfMode() {
    state.weatherMode = 'what-if';
    if (elements.weatherModeBadge) {
      elements.weatherModeBadge.textContent = 'Mode: What-If (Simulated)';
      elements.weatherModeBadge.className = 'badge badge-warn';
    }
  }

  // Live Weather button
  if (elements.btnLiveWeatherPanipat) {
    elements.btnLiveWeatherPanipat.addEventListener('click', () => {
      fetchAndApplyLiveWeather(29.39, 76.97);
    });
  }

  // Slider change listeners
  elements.minTempSlider.addEventListener('input', (e) => {
    elements.minTempVal.textContent = `${e.target.value}°C`;
    markWhatIfMode();
    checkRadiativeAnomaly();
  });
  elements.soilTempSlider.addEventListener('input', (e) => {
    elements.soilTempVal.textContent = `${e.target.value}°C (default, not measured)`;
    markWhatIfMode();
  });
  elements.cloudSlider.addEventListener('input', (e) => {
    const v = parseInt(e.target.value);
    elements.cloudVal.textContent = `${v}% (${v < 25 ? 'Clear Night - Radiative Chill' : 'Cloud Cover'})`;
    markWhatIfMode();
    checkRadiativeAnomaly();
  });
  elements.elevSlider.addEventListener('input', (e) => {
    elements.elevVal.textContent = `${e.target.value}m`;
    markWhatIfMode();
  });
  elements.humiditySlider.addEventListener('input', (e) => {
    elements.humidityVal.textContent = `${e.target.value}%`;
    markWhatIfMode();
  });
  elements.doySlider.addEventListener('input', (e) => {
    const d = parseInt(e.target.value);
    const dateStr = doyToDateString(d);
    elements.doyVal.textContent = `${dateStr} (DOY ${d})`;
    markWhatIfMode();
  });

  // Run Prediction button
  elements.btnRunPrediction.addEventListener('click', runPrediction);

  // Generate Plan button
  elements.btnGeneratePlan.addEventListener('click', generateGemmaPlan);

  // Filter tabs
  elements.categoryFilterTabs.addEventListener('click', (e) => {
    const btn = e.target.closest('.tab-btn');
    if (btn) {
      document.querySelectorAll('#categoryFilterTabs .tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.activeFilter = btn.dataset.filter;
      renderCrops();
    }
  });

  // Audio Play/Pause button
  elements.btnAudioPlay.addEventListener('click', toggleAudioWalkthrough);
  elements.btnQuickAudioWalk.addEventListener('click', () => {
    document.getElementById('outdoorPlanSection').scrollIntoView({ behavior: 'smooth' });
    toggleAudioWalkthrough();
  });

  // Print Pocket Card
  elements.btnPrintPocketCard.addEventListener('click', prepareAndPrintPocketCard);

  // Journal log submit
  elements.journalForm.addEventListener('submit', handleJournalSubmit);
  elements.btnLogOutdoorSession.addEventListener('click', () => {
    document.getElementById('journalSection').scrollIntoView({ behavior: 'smooth' });
    elements.journalMinutesInput.focus();
  });

  // Benchmark Modal
  elements.btnOpenBenchmark.addEventListener('click', openBenchmarkModal);
  elements.btnCloseBenchmark.addEventListener('click', () => elements.benchmarkModal.classList.remove('active'));
  elements.benchmarkModal.addEventListener('click', (e) => {
    if (e.target === elements.benchmarkModal) elements.benchmarkModal.classList.remove('active');
  });

}

// Convert Day of Year to Month & Day (for 2026 autumn)
function doyToDateString(doy) {
  const d = new Date(2026, 0, doy);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// Apply Microclimate Preset
function applyPreset(preset) {
  elements.minTempSlider.value = preset.minTemp;
  elements.minTempVal.textContent = `${preset.minTemp}°C`;

  elements.soilTempSlider.value = preset.soilTemp;
  elements.soilTempVal.textContent = `${preset.soilTemp}°C (default, not measured)`;

  elements.cloudSlider.value = preset.cloud;
  elements.cloudVal.textContent = `${preset.cloud}% (${preset.cloud < 25 ? 'Clear Night' : 'Cloud Cover'})`;

  elements.elevSlider.value = preset.elev;
  elements.elevVal.textContent = `${preset.elev}m`;

  elements.humiditySlider.value = preset.humidity;
  elements.humidityVal.textContent = `${preset.humidity}%`;

  elements.doySlider.value = preset.doy;
  elements.doyVal.textContent = `${doyToDateString(preset.doy)} (DOY ${preset.doy})`;

  checkRadiativeAnomaly();
}

// Check Radiative Anomaly (Clear sky + low temp)
function checkRadiativeAnomaly() {
  const cloud = parseInt(elements.cloudSlider.value);
  const minTemp = parseFloat(elements.minTempSlider.value);
  const isAnomaly = cloud < 20 && minTemp < 5.0;

  if (isAnomaly) {
    elements.radiativeAnomalyText.textContent = '⚠️ Radiative Ground Chill';
    elements.radiativeAnomalyText.className = 'readout-value badge-danger';
  } else {
    elements.radiativeAnomalyText.textContent = 'Normal Cooling';
    elements.radiativeAnomalyText.className = 'readout-value badge-safe';
  }
}

// Initial Data Loading
async function loadInitialData() {
  try {
    const res = await fetch(`${API_BASE}/api/crops`);
    if (res.ok) {
      const data = await res.json();
      state.allCrops = data.crops || FALLBACK_CROPS;
    } else {
      state.allCrops = FALLBACK_CROPS;
    }
  } catch (err) {
    console.warn('Backend API unavailable, using offline crop database:', err);
    state.allCrops = FALLBACK_CROPS;
  }

  // Load Journal
  loadJournalEntries();

  // Run initial prediction
  runPrediction();
}

// Fetch live weather from backend endpoint and apply to inputs
async function fetchAndApplyLiveWeather(lat = 29.39, lon = 76.97) {
  const btn = elements.btnLiveWeatherPanipat;
  const originalHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<div class="spinner" style="width:14px;height:14px;border-width:2px;display:inline-block;margin-right:6px;"></div><span>Fetching live weather...</span>`;
  if (elements.liveWeatherErrorBox) elements.liveWeatherErrorBox.style.display = 'none';

  try {
    const res = await fetch(`${API_BASE}/api/live-weather?lat=${lat}&lon=${lon}`);
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    
    // Fill slider inputs with live data
    const f = data.features;
    state.currentLatitude = f.latitude;
    state.currentLongitude = data.location.longitude;
    state.lastLiveWeather = data;
    state.weatherMode = 'live';

    elements.minTempSlider.value = f.daily_min_temp_c;
    elements.minTempVal.textContent = `${f.daily_min_temp_c}°C`;

    elements.soilTempSlider.value = f.soil_temp_5cm_c;
    elements.soilTempVal.textContent = `${f.soil_temp_5cm_c}°C (default, not measured)`;

    elements.cloudSlider.value = Math.round(f.cloud_cover_pct);
    elements.cloudVal.textContent = `${Math.round(f.cloud_cover_pct)}% (${Math.round(f.cloud_cover_pct) < 25 ? 'Clear Night' : 'Cloud Cover'})`;

    elements.elevSlider.value = Math.round(f.elevation_m);
    elements.elevVal.textContent = `${Math.round(f.elevation_m)}m`;

    elements.humiditySlider.value = Math.round(f.humidity_pct);
    elements.humidityVal.textContent = `${Math.round(f.humidity_pct)}%`;

    elements.doySlider.value = f.day_of_year;
    elements.doyVal.textContent = `${doyToDateString(f.day_of_year)} (DOY ${f.day_of_year})`;

    checkRadiativeAnomaly();

    // Update status UI
    if (elements.weatherModeBadge) {
      elements.weatherModeBadge.textContent = 'Mode: Live Weather (Panipat)';
      elements.weatherModeBadge.className = 'badge badge-fest';
    }
    if (elements.weatherLocationText) {
      elements.weatherLocationText.textContent = `Location: ${data.location.name} (${data.location.latitude}°N, ${data.location.longitude}°E, ${data.location.elevation_m}m)`;
    }
    if (elements.weatherFetchTimeText) {
      const fetchTime = new Date(data.fetched_at).toLocaleTimeString();
      elements.weatherFetchTimeText.textContent = `Fetched: ${fetchTime}`;
    }
    if (elements.defaultedNoticeBadge) {
      elements.defaultedNoticeBadge.textContent = '⚠️ Soil temp & pressure (default, not measured)';
      elements.defaultedNoticeBadge.style.display = 'inline-block';
    }
    if (elements.liveWeatherDetails) elements.liveWeatherDetails.style.display = 'block';
    if (elements.liveTelemetryBreakdown) {
      elements.liveTelemetryBreakdown.textContent = 
        `Real: Min ${f.daily_min_temp_c}°C, Max ${f.daily_max_temp_c}°C, Humidity ${f.humidity_pct}%, Clouds ${f.cloud_cover_pct}% | Defaulted: Soil Temp ${f.soil_temp_5cm_c}°C (default, not measured), Pressure ${f.barometric_pressure_hpa} hPa (default, not measured), Rolling Min ${f.rolling_min_7d_c}°C (default, not measured)`;
    }

    // Run prediction automatically with live weather telemetry
    await runPrediction();

  } catch (err) {
    console.error('Live weather fetch failed:', err);
    if (elements.liveWeatherErrorBox) elements.liveWeatherErrorBox.style.display = 'block';
    if (elements.liveWeatherErrorText) {
      elements.liveWeatherErrorText.textContent = `Open-Meteo unreachable: ${err.message}. Falling back to manual sliders.`;
    }
    if (elements.weatherModeBadge) {
      elements.weatherModeBadge.textContent = 'Mode: Simulated (Fallback)';
      elements.weatherModeBadge.className = 'badge badge-warn';
    }
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalHtml;
  }
}

// Run Tabular Prediction
async function runPrediction() {
  elements.btnRunPrediction.disabled = true;
  elements.btnRunPrediction.innerHTML = `
    <div class="spinner" style="width:16px;height:16px;border-width:2px;"></div>
    <span>Running tabular prediction...</span>
  `;

  const minTemp = parseFloat(elements.minTempSlider.value);
  const soilTemp = parseFloat(elements.soilTempSlider.value);
  const cloud = parseFloat(elements.cloudSlider.value);
  const elev = parseFloat(elements.elevSlider.value);
  const humidity = parseFloat(elements.humiditySlider.value);
  const doy = parseInt(elements.doySlider.value);

  let maxTemp = minTemp + 8.5;
  let pressure = 1013.25;
  let rollingMin = minTemp;
  let lat = state.currentLatitude || 29.39;

  if (state.weatherMode === 'live' && state.lastLiveWeather) {
    const lf = state.lastLiveWeather.features;
    maxTemp = lf.daily_max_temp_c;
    pressure = lf.barometric_pressure_hpa;
    rollingMin = lf.rolling_min_7d_c;
    lat = lf.latitude;
  }

  const payload = {
    latitude: lat,
    elevation_m: elev,
    day_of_year: doy,
    daily_min_temp_c: minTemp,
    daily_max_temp_c: maxTemp,
    soil_temp_5cm_c: soilTemp,
    humidity_pct: humidity,
    cloud_cover_pct: cloud,
    barometric_pressure_hpa: pressure,
    rolling_min_7d_c: rollingMin
  };

  try {
    const res = await fetch(`${API_BASE}/api/predict/frost`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const data = await res.json();
      state.currentPrediction = data.prediction;
      updateFrostGauge(data.prediction);
      renderCrops(data.crop_recommendations);
    } else {
      runLocalPredictionFallback(payload);
    }
  } catch (err) {
    console.warn('Running local browser fallback surrogate:', err);
    runLocalPredictionFallback(payload);
  } finally {
    elements.btnRunPrediction.disabled = false;
    elements.btnRunPrediction.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px;"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
      <span>Run Microclimate Prediction</span>
    `;
  }
}

// Local Tabular Engine Fallback (ensures offline reliability)
function runLocalPredictionFallback(payload) {
  const minTemp = payload.daily_min_temp_c;
  const cloud = payload.cloud_cover_pct;
  const soilTemp = payload.soil_temp_5cm_c;
  
  // Calculate ground chill bonus from low cloud cover
  const radChill = cloud < 20 ? 1.8 : 0.0;
  const effectiveMin = minTemp - radChill;
  
  // Tabular sigmoid probability
  const prob = Math.max(0.02, Math.min(0.98, 1.0 / (1.0 + Math.exp(effectiveMin * 0.85))));
  const days = Math.max(0, Math.round(effectiveMin * 2.8 + (soilTemp * 0.4)));

  let riskLevel = 'Safe Planting Window';
  let riskColor = '#34d399';
  let summary = 'Optimal soil warmth for root development. Garlic, kale, and spinach will establish vigor.';

  if (prob > 0.65) {
    riskLevel = 'Severe Freeze Alert';
    riskColor = '#e76f51';
    summary = 'Hard freeze imminent within 24-48 hours. Mulch garlic cloves & cover tender greens tonight!';
  } else if (prob > 0.35) {
    riskLevel = 'Moderate Frost Watch';
    riskColor = '#f4a261';
    summary = 'Light morning frost expected. Brassicas sweeten up; harvest sensitive root crops soon.';
  }

  const prediction = {
    model_used: 'Local Heuristic (TabPFN unavailable)',
    tabpfn_status: 'TabPFN unavailable',
    frost_probability: prob,
    frost_probability_percent: Math.round(prob * 100),
    days_until_frost: days,
    risk_level: riskLevel,
    risk_color: riskColor,
    action_summary: summary,
    radiative_chill_anomaly: cloud < 20 && minTemp < 5.0
  };

  state.currentPrediction = prediction;
  updateFrostGauge(prediction);
  renderCrops();
}

// Update Frost Gauge & Readouts
function updateFrostGauge(pred) {
  const percent = pred.frost_probability_percent;
  elements.frostProbPercent.textContent = `${percent}%`;
  elements.threatLevelText.textContent = pred.risk_level;
  elements.threatLevelText.style.color = pred.risk_color;
  elements.daysToFrostText.textContent = `~${pred.days_until_frost} Days`;
  elements.frostActionSummaryText.textContent = pred.action_summary;

  // Hero displays
  elements.heroDaysDisplay.textContent = `~${pred.days_until_frost} Days`;
  elements.heroStatusDisplay.textContent = pred.risk_level;
  elements.heroStatusDisplay.style.color = pred.risk_color;

  const isFallback = (pred.tabpfn_status && pred.tabpfn_status.includes('unavailable')) || 
                     (pred.model_used && pred.model_used.includes('Fallback')) ||
                     (pred.model_used && pred.model_used.includes('unavailable'));
  const actualModel = pred.model_used || 'RandomForest (TabPFN unavailable)';
  elements.modelBadge.textContent = actualModel;
  if (elements.headerModelBadge) {
    elements.headerModelBadge.textContent = actualModel;
  }
  if (isFallback) {
    elements.modelBadge.className = 'badge-micro badge-warn';
  } else {
    elements.modelBadge.className = 'badge-micro';
  }

  // Update SVG Gauge circle (perimeter = 2 * PI * 42 ~= 263.9)
  const circumference = 264;
  const offset = circumference - (percent / 100) * circumference;
  elements.gaugeBar.style.strokeDashoffset = offset;
  elements.gaugeBar.style.stroke = pred.risk_color;
}

// Render Crops Matrix
function renderCrops(cropRecommendations = null) {
  const crops = cropRecommendations || state.allCrops;
  const filtered = crops.filter(c => {
    if (state.activeFilter === 'all') return true;
    return c.category === state.activeFilter;
  });

  elements.cropsGrid.innerHTML = filtered.map(crop => {
    const isSelected = state.selectedCropIds.includes(crop.id);
    const score = crop.suitability_score !== undefined ? crop.suitability_score : 92;
    
    let scoreClass = '';
    if (score < 50) scoreClass = 'badge-late';
    else if (score < 75) scoreClass = 'badge-warn';

    return `
      <div class="crop-card ${isSelected ? 'selected' : ''}" data-crop-id="${crop.id}" onclick="toggleCropSelect('${crop.id}')">
        <div class="crop-card-top">
          <div>
            <div class="crop-name">${crop.name}</div>
            <div class="crop-scientific">${crop.scientific || crop.category}</div>
          </div>
          <span class="suitability-badge ${scoreClass}">${score}% Match</span>
        </div>

        <div class="crop-meta-row">
          <span>Tolerance: ${crop.frost_tolerance || 'Hardy'}</span>
          <span class="knuckle-tag">📏 ${crop.planting_depth_cm || 5}cm deep</span>
        </div>

        <div class="crop-soil-meta" style="font-size: 0.74rem; color: #94a3b8; margin: 4px 0 6px 0;">
          <span>🌱 Soil temp: ${crop.current_soil_temp_c !== undefined ? crop.current_soil_temp_c + '°C (default, not measured)' : '22.0°C (default, not measured)'}</span>
        </div>

        <div class="crop-tip">
          ${crop.outdoor_action || crop.touch_grass_tip}
        </div>

        <div class="crop-card-footer">
          <label class="crop-select-checkbox">
            <input type="checkbox" ${isSelected ? 'checked' : ''} onclick="event.stopPropagation(); toggleCropSelect('${crop.id}')">
            <span>Include in Outdoor Plan</span>
          </label>
        </div>
      </div>
    `;
  }).join('');

  updateSelectionDisplay();
}

// Toggle Crop Selection
window.toggleCropSelect = function(cropId) {
  if (state.selectedCropIds.includes(cropId)) {
    if (state.selectedCropIds.length > 1) {
      state.selectedCropIds = state.selectedCropIds.filter(id => id !== cropId);
    }
  } else {
    state.selectedCropIds.push(cropId);
  }
  renderCrops();
  updateSelectionDisplay();
};

function updateSelectionDisplay() {
  const count = state.selectedCropIds.length;
  elements.selectedCountDisplay.textContent = `${count} crop${count !== 1 ? 's' : ''} selected`;
}

// Generate Gemma Outdoor Action Plan
async function generateGemmaPlan() {
  elements.btnGeneratePlan.disabled = true;
  elements.btnGeneratePlan.innerHTML = `
    <div class="spinner" style="width:16px;height:16px;border-width:2px;"></div>
    <span>Gemma Crafting Dirt Guide...</span>
  `;

  const payload = {
    microclimate: {
      elevation_m: parseFloat(elements.elevSlider.value),
      day_of_year: parseInt(elements.doySlider.value),
      daily_min_temp_c: parseFloat(elements.minTempSlider.value),
      daily_max_temp_c: parseFloat(elements.minTempSlider.value) + 9.5,
      soil_temp_5cm_c: parseFloat(elements.soilTempSlider.value),
      humidity_pct: parseFloat(elements.humiditySlider.value),
      cloud_cover_pct: parseFloat(elements.cloudSlider.value),
      barometric_pressure_hpa: 1020.0,
      rolling_min_7d_c: parseFloat(elements.minTempSlider.value) + 0.8
    },
    selected_crop_ids: state.selectedCropIds
  };

  try {
    const res = await fetch(`${API_BASE}/api/generate/plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const data = await res.json();
      state.currentPlan = data.gemma_plan;
      renderOutdoorPlan(data.gemma_plan);
    } else {
      renderLocalGemmaPlan();
    }
  } catch (err) {
    console.warn('Backend unavailable, using local Gemma engine:', err);
    renderLocalGemmaPlan();
  } finally {
    elements.btnGeneratePlan.disabled = false;
    elements.btnGeneratePlan.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
      <span>Generate Gemma Outdoor Action Plan</span>
    `;
    document.getElementById('outdoorPlanSection').scrollIntoView({ behavior: 'smooth' });
  }
}

// Local Gemma Fallback Plan
function renderLocalGemmaPlan() {
  const chosen = state.allCrops.filter(c => state.selectedCropIds.includes(c.id));
  const names = chosen.map(c => c.name);
  const days = state.currentPrediction ? state.currentPrediction.days_until_frost : 12;

  const plan = {
    source: "offline template",
    chores: [
      {
        step: 1,
        title: "Trench & Loosen Soil Bed",
        duration: "15 mins",
        action: `Loosen the top 15cm of soil with a garden fork. Press cloves or seeds into earth: ${chosen[0]?.knuckles || '2 knuckles deep'}.`,
        tools: ["Garden fork or hand trowel", "Compost or bone meal"]
      },
      {
        step: 2,
        title: `Plant ${names.slice(0, 2).join(' & ')}`,
        duration: "15 mins",
        action: "Position bulbs pointy tip up, firm soil down firmly with your palm to establish seed-to-earth contact.",
        tools: ["Watering can with fine rose"]
      },
      {
        step: 3,
        title: "Thermal Autumn Leaf Blanket",
        duration: "10 mins",
        action: `Tuck the bed in with 10cm of shredded dry autumn leaves to insulate soil microbes against the frost predicted in ~${days} days.`,
        tools: ["Rake", "Dry fallen leaves or clean straw"]
      }
    ],
    touch_grass_sensory: "Take 60 seconds before you start: Kneel down, press your bare fingertips into the cool earth. Notice the rich fungal smell of autumn soil preparing for winter rest. Listen to the wind through the trees. Your screen is in your pocket.",
    companion_synergy: [
      {
        pair: "Garlic + Spinach",
        benefit: "(Commonly said / unverified) Garlic sulfur emissions are said to deter underground root cutworms while spinach roots shade garlic cloves from winter freeze heaving."
      }
    ],
    audio_script: `Welcome out to your garden. Take a deep breath of the crisp air. According to our microclimate analysis, you have about ${days} days before the killing frost arrives. We are planting ${names.join(' and ')}. Put your phone away in your pocket, grab your hand trowel, and let's tuck these roots into the earth. First, loosen the soil bed about six inches deep...`
  };

  state.currentPlan = plan;
  renderOutdoorPlan(plan);
}

// Render Outdoor Plan into UI
function renderOutdoorPlan(plan) {
  const planSourceEl = document.getElementById('planSourceValue');
  if (planSourceEl) {
    planSourceEl.textContent = plan.source || 'offline template';
  }

  elements.choresList.innerHTML = (plan.chores || []).map(c => `
    <div class="chore-item">
      <div class="chore-num">${c.step}</div>
      <div class="chore-body">
        <div class="chore-title-row">
          <span class="chore-title">${c.title}</span>
          <span class="chore-duration">${c.duration}</span>
        </div>
        <p class="chore-action">${c.action}</p>
        <span class="chore-tools">🔧 Tools: ${(c.tools || []).join(', ')}</span>
      </div>
    </div>
  `).join('');

  elements.sensoryBoxText.textContent = `"${plan.touch_grass_sensory}"`;
  
  if (plan.companion_synergy && plan.companion_synergy.length > 0) {
    const syn = plan.companion_synergy[0];
    elements.synergyContentText.textContent = `${syn.pair}: ${syn.benefit}`;
  }
}

// Hands-Free Audio Walkthrough (Web Speech API)
function toggleAudioWalkthrough() {
  if (state.isPlayingAudio) {
    stopAudio();
  } else {
    startAudio();
  }
}

function startAudio() {
  const script = state.currentPlan?.audio_script || 
    "Welcome out to your garden. Put your phone in your pocket, grab your trowel, and take a deep breath. Let's touch grass and work the soil together.";

  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(script);
    utterance.rate = 0.95;
    utterance.pitch = 1.0;

    // Pick warm natural voice if available
    const voices = window.speechSynthesis.getVoices();
    const naturalVoice = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Samantha')));
    if (naturalVoice) utterance.voice = naturalVoice;

    utterance.onstart = () => {
      state.isPlayingAudio = true;
      elements.audioWaveform.classList.add('active');
      elements.audioPlayIcon.innerHTML = '<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>';
      elements.audioTrackTitle.textContent = 'Playing: Garden Walkthrough (Hands-Free Mode Active)';
    };

    utterance.onend = () => {
      stopAudio();
    };

    utterance.onerror = () => {
      stopAudio();
    };

    state.speechSynthUtterance = utterance;
    window.speechSynthesis.speak(utterance);
  } else {
    alert("Speech audio is ready. Grab your tools and step outside!");
  }
}

function stopAudio() {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
  state.isPlayingAudio = false;
  elements.audioWaveform.classList.remove('active');
  elements.audioPlayIcon.innerHTML = '<polygon points="5 3 19 12 5 21 5 3"/>';
  elements.audioTrackTitle.textContent = 'Garden Walkthrough: Frost Prep & Planting Session';
}

// Prepare & Print Pocket Field Card
function prepareAndPrintPocketCard() {
  const pred = state.currentPrediction || { frost_probability_percent: 32, days_until_frost: 12 };
  const chosen = state.allCrops.filter(c => state.selectedCropIds.includes(c.id));
  
  elements.printCardDate.textContent = `Autumn ${new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;
  const modelName = pred.model_used || 'RandomForest (TabPFN unavailable)';
  elements.printWeatherBar.textContent = `${modelName} Frost Risk: ${pred.frost_probability_percent}% | Window: ~${pred.days_until_frost} Days to Freeze`;

  elements.printCropsSection.innerHTML = `
    <strong>Target Crops:</strong><br>
    ${chosen.map(c => `• ${c.name} — Depth: ${c.knuckles || '2 knuckles (5cm)'}`).join('<br>')}
  `;

  const chores = state.currentPlan?.chores || [
    { title: "Prep bed", action: "Loosen 15cm soil with fork" },
    { title: "Sow seeds", action: "Plant at recommended depth" },
    { title: "Mulch", action: "Cover with 10cm dry leaves" }
  ];

  elements.printChoresSection.innerHTML = `
    <strong>Action Chores:</strong><br>
    ${chores.map((c, i) => `${i+1}. ${c.title}: ${c.action}`).join('<br>')}
  `;

  window.print();
}

// Handle Journal Submission
async function handleJournalSubmit(e) {
  e.preventDefault();
  const minutes = parseInt(elements.journalMinutesInput.value) || 30;
  const soilFeel = elements.journalSoilFeelSelect.value;
  const notes = elements.journalNotesInput.value.trim() || 'Worked in the autumn soil with bare hands.';
  const chosenNames = state.allCrops.filter(c => state.selectedCropIds.includes(c.id)).map(c => c.name);

  const newEntry = {
    date: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
    minutes_outside: minutes,
    crops_planted: chosenNames,
    notes: notes,
    soil_feel: soilFeel
  };

  try {
    const res = await fetch(`${API_BASE}/api/journal`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newEntry)
    });
    if (res.ok) {
      loadJournalEntries();
    } else {
      saveLocalJournalEntry(newEntry);
    }
  } catch (err) {
    saveLocalJournalEntry(newEntry);
  }

  // Update UI stats
  elements.heroStreakDisplay.textContent = `${minutes}m`;
  elements.journalNotesInput.value = '';
  alert(`🌿 Outdoor dirt session logged! You spent ${minutes} minutes touching grass today.`);
}

function saveLocalJournalEntry(entry) {
  const entries = JSON.parse(localStorage.getItem('frostsprout_journal') || '[]');
  entries.unshift(entry);
  localStorage.setItem('frostsprout_journal', JSON.stringify(entries));
  renderJournalHistory(entries);
}

async function loadJournalEntries() {
  try {
    const res = await fetch(`${API_BASE}/api/journal`);
    if (res.ok) {
      const data = await res.json();
      renderJournalHistory(data.entries || []);
      return;
    }
  } catch (e) {}

  const entries = JSON.parse(localStorage.getItem('frostsprout_journal') || '[]');
  if (entries.length === 0) {
    // Demo entry
    entries.push({
      date: 'Oct 9, 2026',
      minutes_outside: 45,
      crops_planted: ['Hardneck Garlic', 'French Breakfast Radish'],
      notes: 'Tucked 32 cloves into the cold dirt. Soil was crumbly and dark. Hand knuckles got properly dirty!',
      soil_feel: 'Cool, crumbly dark loam'
    });
  }
  renderJournalHistory(entries);
}

function renderJournalHistory(entries) {
  state.journalEntries = entries;
  elements.streakBadgeText.textContent = `🔥 ${Math.min(entries.length, 5)} Day Streak`;
  
  if (entries.length === 0) {
    elements.journalHistoryList.innerHTML = `<div style="color:var(--text-dim);font-size:0.8rem;">No dirt sessions logged yet. Step outside!</div>`;
    return;
  }

  elements.journalHistoryList.innerHTML = entries.slice(0, 4).map(e => `
    <div class="history-item">
      <div class="history-item-top">
        <span><strong>${e.minutes_outside} mins</strong> • ${e.soil_feel || 'Outdoor Bed'}</span>
        <span>${e.date}</span>
      </div>
      <div class="history-item-notes">${e.notes}</div>
    </div>
  `).join('');
}

// Open Benchmark Modal
async function openBenchmarkModal() {
  elements.benchmarkModal.classList.add('active');
  elements.benchmarkModalBody.innerHTML = `
    <div class="loading-state"><div class="spinner"></div><span>Running microclimate benchmarks across TabPFN, XGBoost & Random Forest...</span></div>
  `;

  try {
    const res = await fetch(`${API_BASE}/api/benchmark`);
    if (res.ok) {
      const data = await res.json();
      renderBenchmarkTable(data);
      return;
    }
  } catch (e) {}

  // If backend returns benchmark data, render it
  elements.benchmarkModalBody.innerHTML = `
    <div style="margin-bottom:1rem;font-size:0.85rem;color:var(--text-sub);">
      Note: Benchmark evaluated strictly on synthetic microclimate data (seed=42).
    </div>
    <div style="color:var(--danger);font-size:0.9rem;">Unable to load live benchmark from backend API. Run <code>python backend/benchmark.py</code> directly.</div>
  `;
}

function renderBenchmarkTable(data) {
  const models = data.models || {};
  elements.benchmarkModalBody.innerHTML = `
    <div style="margin-bottom:1.25rem;font-size:0.85rem;color:var(--text-sub);line-height:1.5;">
      Benchmark evaluated on synthetic microclimate data (seed=42). TabPFN model weights require one-time Prior Labs license authentication.
    </div>
    <table class="benchmark-table">
      <thead>
        <tr>
          <th>Model</th>
          <th>ROC-AUC</th>
          <th>Accuracy</th>
          <th>Log-Loss</th>
          <th>Fit Time</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        ${Object.entries(models).map(([name, m]) => {
          const accStr = typeof m.accuracy === 'number' ? `${(m.accuracy * 100).toFixed(1)}%` : (m.accuracy || 'NOT VERIFIED');
          const timeStr = typeof m.fit_time_seconds === 'number' ? `${m.fit_time_seconds.toFixed(4)}s` : (m.fit_time_seconds || 'NOT VERIFIED');
          return `
            <tr>
              <td><strong>${name}</strong></td>
              <td>${m.roc_auc || 'NOT VERIFIED'}</td>
              <td>${accStr}</td>
              <td>${m.log_loss || 'NOT VERIFIED'}</td>
              <td>${timeStr}</td>
              <td>${m.status || (m.hyperparameter_tuning_needed ? 'Baseline' : 'N/A')}</td>
            </tr>
          `;
        }).join('')}
      </tbody>
    </table>
  `;
}
