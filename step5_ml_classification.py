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

print("2. Fetching imagery and calculating indices...")
collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
    .filterBounds(roi) \
    .filterDate('2025-11-01', '2026-06-30') \
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 60)) 

image = collection.median().clip(roi)

# Add NDWI (Water) and NDVI (Vegetation) as bands so the AI can use them as features
ndwi = image.normalizedDifference(['B3', 'B8']).rename('NDWI')
ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
image = image.addBands([ndwi, ndvi])

print("3. Creating training data for the AI...")
# We are hardcoding a few coordinate points to teach the AI what is what.
# Class 0 = Water/Wetland, Class 1 = Healthy Vegetation, Class 2 = Built-up/Bare Soil
points = ee.FeatureCollection([
    ee.Feature(ee.Geometry.Point([31.015, -17.805]), {'class': 0}), # Known Wetland center
    ee.Feature(ee.Geometry.Point([31.013, -17.802]), {'class': 0}), # Known Wetland edge
    ee.Feature(ee.Geometry.Point([31.016, -17.810]), {'class': 1}), # Known Vegetation
    ee.Feature(ee.Geometry.Point([31.010, -17.805]), {'class': 1}), # Known Vegetation
    ee.Feature(ee.Geometry.Point([31.006, -17.810]), {'class': 2}), # Known Urban/Concrete (Mabelreign side)
    ee.Feature(ee.Geometry.Point([31.022, -17.800]), {'class': 2}), # Known Urban/Concrete
])

# Select the satellite bands the model will learn from
bands = ['B2', 'B3', 'B4', 'B8', 'NDWI', 'NDVI']

# Tell the system to extract the mathematical values at our training points
training_data = image.select(bands).sampleRegions(
    collection=points,
    properties=['class'],
    scale=10 # Sentinel-2 is 10-meters per pixel
)

print("4. Training the Random Forest Machine Learning Model...")
# Train a Random Forest classifier with 10 decision trees
classifier = ee.Classifier.smileRandomForest(10).train(
    features=training_data,
    classProperty='class',
    inputProperties=bands
)

print("5. Classifying the entire Monavale Vlei area...")
# Apply the trained AI model to the whole image
classified_image = image.select(bands).classify(classifier)

# Map our 3 classes to colors: 0=Blue, 1=Green, 2=Red
class_vis = {
    'min': 0,
    'max': 2,
    'palette': ['0000FF', '00FF00', 'FF0000'], 
    'dimensions': 800
}

try:
    url = classified_image.getThumbUrl(class_vis)
    print("\n--- SUCCESS! ---")
    print("Hold 'Ctrl' (or 'Cmd') and click to see your Machine Learning Map:")
    print("Blue = Wetland/Water | Green = Vegetation | Red = Urban/Encroachment")
    print(f"\n{url}\n")
except Exception as e:
    print("\nFailed to generate image URL. Error details:", e)