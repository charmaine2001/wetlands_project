import ee
import json

PROJECT_ID = 'bevisioneerswetlandsproject'

# 1. Initialize Earth Engine
try:
    ee.Initialize(project=PROJECT_ID)
    print("1. Earth Engine initialized successfully.")
except Exception as e:
    print("Initialization failed.", e)
    exit()

# 2. Define Monavale Vlei ROI
roi = ee.Geometry.Polygon([
    [31.005, -17.815], [31.025, -17.815], 
    [31.025, -17.795], [31.005, -17.795], 
    [31.005, -17.815]
])

# 3. Helper function to apply scaling factors for Landsat Collection 2 Level 2
# This converts raw sensor values into physical surface reflectance values
def scale_landsat(image):
    optical_bands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
    return image.addBands(optical_bands, overwrite=True)

# 4. Helper function to calculate NDWI using Landsat 5 (Active in 1996)
# Landsat 5 Bands: SR_B2 is Green, SR_B4 is Near-Infrared (NIR)
def get_landsat5_ndwi_mask(start_date, end_date):
    collection = ee.ImageCollection('LANDSAT/LT05/C02/T1_L2') \
        .filterBounds(roi) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUD_COVER', 50)) \
        .map(scale_landsat)
    
    image = collection.median().clip(roi)
    ndwi = image.normalizedDifference(['SR_B2', 'SR_B4']).rename('NDWI')
    # Threshold: NDWI >= -0.1 represents saturated soil/wetland conditions
    return ndwi.gte(-0.1)

# 5. Helper function to calculate NDWI using Landsat 8 (Active in 2026)
# Landsat 8 Bands: SR_B3 is Green, SR_B5 is Near-Infrared (NIR)
def get_landsat8_ndwi_mask(start_date, end_date):
    collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
        .filterBounds(roi) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUD_COVER', 50)) \
        .map(scale_landsat)
    
    image = collection.median().clip(roi)
    ndwi = image.normalizedDifference(['SR_B3', 'SR_B5']).rename('NDWI')
    return ndwi.gte(-0.1)

print("2. Fetching Landsat 5 data (1996 Baseline)...")
# Using 1995-1997 to get a clean, cloudless median composite representing ~30 years ago
baseline_mask = get_landsat5_ndwi_mask('1995-01-01', '1997-12-31')

print("3. Fetching Landsat 8 data (2026 Current)...")
# Using current 2025-2026 data
current_mask = get_landsat8_ndwi_mask('2025-01-01', '2026-06-30')

print("4. Calculating 30-year environmental change...")
# Isolate areas that were wet in 1996 (1) but are dry now (0)
wetland_loss = baseline_mask.And(current_mask.Not())

# Landsat pixel area is 30m x 30m = 900 square meters
pixel_area = ee.Image.pixelArea()

loss_area_image = wetland_loss.multiply(pixel_area)
loss_stats = loss_area_image.reduceRegion(
    reducer=ee.Reducer.sum(),
    geometry=roi,
    scale=30, # Landsat native resolution is 30m
    maxPixels=1e9
)

baseline_area_image = baseline_mask.multiply(pixel_area)
baseline_stats = baseline_area_image.reduceRegion(
    reducer=ee.Reducer.sum(),
    geometry=roi,
    scale=30,
    maxPixels=1e9
)

try:
    loss_sq_meters = loss_stats.getInfo().get('NDWI', 0)
    baseline_sq_meters = baseline_stats.getInfo().get('NDWI', 0)
    
    loss_hectares = loss_sq_meters / 10000.0
    baseline_hectares = baseline_sq_meters / 10000.0
    loss_percentage = (loss_hectares / baseline_hectares * 100) if baseline_hectares > 0 else 0
    
    print("\n=============================================")
    print("      30-YEAR LANDSAT HISTORICAL ANALYSIS     ")
    print("=============================================")
    print(f"Wetland Area (1996): {baseline_hectares:.2f} Hectares")
    print(f"Wetland Area Lost:   {loss_hectares:.2f} Hectares")
    print(f"Percentage Lost:     {loss_percentage:.1f}%")
    
    anomaly_alert = {
        "status": "CRITICAL" if loss_percentage > 15 else "STABLE",
        "region": "Monavale Vlei, Harare",
        "timeframe": "1996 to 2026 (30-Year Trend)",
        "metrics": {
            "baseline_1996_hectares": round(baseline_hectares, 2),
            "lost_hectares": round(loss_hectares, 2),
            "loss_percentage": round(loss_percentage, 1)
        },
        "trigger_action": "High-priority policy alert: Significant multi-decadal ecosystem reduction detected." if loss_percentage > 15 else "Normal historical variance."
    }
    
    print("\n--- DECADAL API WEBHOOK PAYLOAD ---")
    print(json.dumps(anomaly_alert, indent=2))
    
    # Generate visualization
    loss_vis = {
        'min': 0,
        'max': 1,
        'palette': ['#000000', '#FF3333'], # Dark background, lost wetland zones highlight in neon red
        'dimensions': 800
    }
    
    loss_url = wetland_loss.getThumbUrl(loss_vis)
    print("\n--- VISUAL PROOF OF 30-YEAR LOSS ---")
    print("Click the link to see the historical loss footprint (RED):")
    print(loss_url)
    print("\n")

except Exception as e:
    print("Error calculating change metrics:", e)