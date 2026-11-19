import ee

PROJECT_ID = 'bevisioneerswetlandsproject' 

# 1. Initialize Earth Engine
try:
    ee.Initialize(project=PROJECT_ID)
except Exception as e:
    print("Initialization failed.", e)
    exit()

print("Earth Engine initialized. Fetching satellite data...")

# 2. Define the Region of Interest (Monavale Vlei)
monavale_coordinates = [
    [31.005, -17.815], [31.025, -17.815], 
    [31.025, -17.795], [31.005, -17.795], 
    [31.005, -17.815]
]
roi = ee.Geometry.Polygon(monavale_coordinates)

# 3. Fetch Sentinel-2 Surface Reflectance Data
# We are looking at Jan 1, 2026 to May 31, 2026 (Good for tracking post-rainy season water)
collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
    .filterBounds(roi) \
    .filterDate('2026-01-01', '2026-05-31') \
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) # Keep only images with < 20% clouds

# 4. Create a cloud-free composite and clip it strictly to our Monavale boundary
cloud_free_image = collection.median().clip(roi)

# 5. Generate a visual representation (True Color - what the human eye sees)
# Sentinel-2 Band 4 is Red, Band 3 is Green, Band 2 is Blue
vis_params = {
    'bands': ['B4', 'B3', 'B2'], 
    'min': 0,      # Minimum reflectance value
    'max': 3000,   # Maximum reflectance value (adjusts brightness)
    'dimensions': 800 # Size of the image to generate
}

# 6. Get a URL to view the image
try:
    image_url = cloud_free_image.getThumbUrl(vis_params)
    print("\nSUCCESS! We processed the satellite imagery.")
    print("Hold 'Ctrl' (or 'Cmd' on Mac) and click the link below to see Monavale Vlei from space:")
    print(f"\n{image_url}\n")
except Exception as e:
    print("Failed to generate image URL.", e)