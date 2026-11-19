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

# 3. Define helper function to get an NDWI Mask
def get_wetland_mask(start_date, end_date):
    collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(roi) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 60))
    
    # Generate median composite
    image = collection.median().clip(roi)
    
    # Compute NDWI
    ndwi = image.normalizedDifference(['B3', 'B8'])
    
    # Threshold NDWI: values >= -0.1 represent wet soil or surface water
    # This creates a binary mask (1 for wetland, 0 for dry land)
    return ndwi.gte(-0.1)

print("2. Fetching baseline (Past) and comparison (Present) datasets...")
# Baseline: Nov 2015 - Jun 2022
baseline_mask = get_wetland_mask('2015-11-01', '2022-06-30')

# Comparison: Nov 2023 - Jun 2026
current_mask = get_wetland_mask('2023-11-01', '2026-06-30')

print("3. Calculating environmental change...")
# Identify where wetland has been lost:
# baseline had wetland (1) AND current does NOT have wetland (0)
wetland_loss = baseline_mask.And(current_mask.Not())

# Calculate area of a single pixel in square meters (10m x 10m = 100 sqm)
pixel_area = ee.Image.pixelArea()

# Multiply the binary loss mask by the pixel area to get the area of each lost pixel
loss_area_image = wetland_loss.multiply(pixel_area)

# Sum up all the lost pixel areas inside our ROI
loss_stats = loss_area_image.reduceRegion(
    reducer=ee.Reducer.sum(),
    geometry=roi,
    scale=10,
    maxPixels=1e9
)

# Sum up baseline wetland area to calculate percentage loss
baseline_area_image = baseline_mask.multiply(pixel_area)
baseline_stats = baseline_area_image.reduceRegion(
    reducer=ee.Reducer.sum(),
    geometry=roi,
    scale=10,
    maxPixels=1e9
)

# Retrieve raw numbers from the GEE servers
try:
    loss_sq_meters = loss_stats.getInfo().get('ndwi', 0)
    baseline_sq_meters = baseline_stats.getInfo().get('ndwi', 0)
    
    # Convert square meters to Hectares (1 Hectare = 10,000 square meters)
    loss_hectares = loss_sq_meters / 10000.0
    baseline_hectares = baseline_sq_meters / 10000.0
    
    loss_percentage = (loss_hectares / baseline_hectares * 100) if baseline_hectares > 0 else 0
    
    print("\n--- ANALYSIS COMPLETE ---")
    print(f"Baseline Wetland Area: {baseline_hectares:.2f} Hectares")
    print(f"Wetland Lost: {loss_hectares:.2f} Hectares")
    print(f"Percentage of Wetland Destroyed: {loss_percentage:.1f}%")
    
    # 4. Construct Webhook Trigger Payload
    # This JSON data structure is what your backend will use to trigger alerts
    anomaly_alert = {
        "status": "CRITICAL" if loss_percentage > 5 else "STABLE",
        "region": "Monavale Vlei, Harare",
        "metrics": {
            "baseline_hectares": round(baseline_hectares, 2),
            "lost_hectares": round(loss_hectares, 2),
            "loss_ratio": round(loss_percentage, 1)
        },
        "trigger_action": "Notify local environmental agencies and send community USSD broadcast." if loss_percentage > 5 else "No action required."
    }
    
    print("\n--- MOCK API WEBHOOK PAYLOAD ---")
    print(json.dumps(anomaly_alert, indent=2))
    
    # 5. Generate visual URL of the exact loss zones (Loss shown in Red)
    loss_vis = {
        'min': 0,
        'max': 1,
        'palette': ['#000000', '#FF0000'], # Background is black, lost areas are bright red
        'dimensions': 800
    }
    
    loss_url = wetland_loss.getThumbUrl(loss_vis)
    print("\n--- VISUAL PROOF OF LOSS ---")
    print("Hold 'Ctrl' (or 'Cmd') and click the link below to see the exact locations of wetland loss (in RED):")
    print(loss_url)
    print("\n")

except Exception as e:
    print("Error calculating change metrics:", e)