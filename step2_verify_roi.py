import ee

# Initialize the Earth Engine library
# This connects your local script to Google's cloud servers
try:
    # Explicitly pass the project ID during initialization
    ee.Initialize(project="bevisioneerswetlandsproject")
    print("Earth Engine successfully initialized!")
except Exception as e:
    print("Initialization failed. Make sure you ran 'earthengine authenticate'.")
    print(e)
    exit()
# Define the coordinates for Monavale Vlei, Harare, Zimbabwe
# Coordinates are defined as: [longitude, latitude]
# We build a polygon using 4 corners (and closing it with the 1st corner)
monavale_coordinates = [
    [31.005, -17.815],  # Bottom-Left
    [31.025, -17.815],  # Bottom-Right
    [31.025, -17.795],  # Top-Right
    [31.005, -17.795],  # Top-Left
    [31.005, -17.815]   # Close the loop back at Bottom-Left
]

# Convert the coordinates into an Earth Engine Geometry Polygon object
roi = ee.Geometry.Polygon(monavale_coordinates)

# Print out the spatial metadata to verify the object exists in the cloud
print("\n--- Region of Interest (ROI) Created ---")
print(f"Geometry Type: {roi.type().getInfo()}")
print(f"Bounding Coordinates: {roi.coordinates().getInfo()}")