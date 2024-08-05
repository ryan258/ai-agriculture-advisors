#!/bin/bash

# Create directories
mkdir -p src/{config,models,routes,controllers,services,utils}
mkdir -p data
mkdir -p tests/{unit,integration}

# Create main server file
touch src/server.js

# Create config file
touch src/config/database.js

# Create model files
touch src/models/agriculturalData.js
touch src/models/userQuery.js

# Create route file
touch src/routes/api.js

# Create controller files
touch src/controllers/agricultureExpert.js
touch src/controllers/climateAnalyst.js
touch src/controllers/commoditiesSpecialist.js
touch src/controllers/agritechResearcher.js
touch src/controllers/supplyChainAnalyst.js

# Create service files
touch src/services/llamaService.js
touch src/services/dataCollectionService.js
touch src/services/insightGenerationService.js

# Create utility files
touch src/utils/llamaHelper.js
touch src/utils/dataPreprocessor.js

# Create data files
touch data/cropData.json
touch data/climateData.json
touch data/marketData.json

# Create README
touch README.md

echo "Project structure created successfully!"