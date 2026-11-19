import ee

PROJECT_ID = 'bevisioneerswetlandsproject' 

# 1. Initialize Earth Engine
try:
    ee.Initialize(project=PROJECT_ID)
    print("1. Earth Engine initialized.")
except Exception as e:
    print("Initialization failed.", e)
    exit()

# 2. Define Monavale Vlei ROI
roi = ee.Geometry.Polygon([
    [31.005, -17.815], [31.025, -17.815], 
    [31.025, -17.795], [31.005, -17.795], 
    [31.005, -17.815]
])

# 3. Fetch and filter the cloud-free median image (Just like Step 3)
print("2. Fetching satellite data...")
collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
    .filterBounds(roi) \
    .filterDate('2025-11-01', '2026-06-30') \
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 60)) 

image = collection.median().clip(roi)

print("3. Calculating Spectral Indices (Math on the satellite bands)...")

# --- CALCULATE NDWI (Water) ---
# Formula: (Green - NIR) / (Green + NIR)
# Sentinel-2 Bands: B3 is Green, B8 is NIR
ndwi = image.normalizedDifference(['B3', 'B8']).rename('NDWI')

# --- CALCULATE NDVI (Vegetation) ---
# Formula: (NIR - Red) / (NIR + Red)
# Sentinel-2 Bands: B8 is NIR, B4 is Red
ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')


print("4. Generating visualization URLs...")

# Visual parameters for WATER (NDWI)
# Values range from -1 to 1. Higher values (closer to 1) mean more water.
# We map low values to brown/white, and high values to deep blue.
ndwi_vis = {
    'min': -0.5, 
    'max': 0.5, 
    'palette': ['#a6611a', '#dfc27d', '#f5f5f5', '#80cdc1', '#018571', '#0000ff'],
    'dimensions': 800
}

# Visual parameters for VEGETATION (NDVI)
# Higher values mean healthier vegetation.
# We map low values to white/yellow, and high values to dark green.
ndvi_vis = {
    'min': 0.0, 
    'max': 0.8, 
    'palette': ['#ffffff', '#ce7e45', '#df923d', '#f1b555', '#fcd163', '#99b718', '#74a901', '#66a000', '#529400', '#3e8601', '#207401', '#056201', '#004c00', '#023b01', '#012e01', '#011d01', '#011301'],
    'dimensions': 800
}

try:
    ndwi_url = ndwi.getThumbUrl(ndwi_vis)
    ndvi_url = ndvi.getThumbUrl(ndvi_vis)
    
    print("\n--- SUCCESS! ---")
    print("Hold 'Ctrl' (or 'Cmd') and click to see the WATER MAP (Blue = High Moisture):")
    print(ndwi_url)
    
    print("\nHold 'Ctrl' (or 'Cmd') and click to see the VEGETATION MAP (Dark Green = Healthy Reeds):")
    print(ndvi_url)
    print("\n")
except Exception as e:
    print("\nFailed to generate image URLs. Error details:")
    print(e)