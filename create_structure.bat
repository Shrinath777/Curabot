@echo off
echo Creating CuraBot project structure...
echo.

REM Navigate to your project directory
cd /d C:\projects\tcs project\curabot

REM Create main directories
mkdir backend\agents backend\core backend\knowledge backend\data\ontologies backend\api frontend\public frontend\src\components\layout frontend\src\components\chat frontend\src\components\agents frontend\src\components\diagnosis frontend\src\components\ui frontend\src\services frontend\src\store frontend\src\hooks frontend\src\types frontend\src\utils tests 2>nul

echo Directory structure created.

REM Create backend Python files
echo. > backend\__init__.py
echo. > backend\agents\__init__.py
echo. > backend\agents\symptom_normalizer.py
echo. > backend\agents\hypothesis_generator.py
echo. > backend\agents\evidence_evaluator.py
echo. > backend\agents\hypothesis_reviser.py
echo. > backend\agents\diagnostic_strategist.py
echo. > backend\agents\self_critique.py
echo. > backend\core\__init__.py
echo. > backend\core\state.py
echo. > backend\core\graph.py
echo. > backend\core\supervisor.py
echo. > backend\knowledge\__init__.py
echo. > backend\knowledge\disease_db.py
echo. > backend\knowledge\vector_store.py
echo. > backend\knowledge\loader.py
echo. > backend\api\__init__.py
echo. > backend\api\routes.py
echo. > backend\api\websocket.py
echo. > backend\main.py

REM Create JSON data files
echo {} > backend\data\diseases.json
echo [] > backend\data\synthetic_cases.json

echo Backend files created.

REM Create frontend files
echo. > frontend\index.html
echo {} > frontend\package.json
echo. > frontend\vite.config.ts
echo. > frontend\tailwind.config.js
echo. > frontend\postcss.config.js
echo. > frontend\tsconfig.json
echo. > frontend\public\favicon.ico

REM Create frontend source files
echo. > frontend\src\main.tsx
echo. > frontend\src\App.tsx
echo. > frontend\src\vite-env.d.ts
echo. > frontend\src\index.css

REM Create component files
echo. > frontend\src\components\layout\Header.tsx
echo. > frontend\src\components\layout\AnimatedBackground.tsx
echo. > frontend\src\components\layout\GlassCard.tsx
echo. > frontend\src\components\chat\ChatInterface.tsx
echo. > frontend\src\components\chat\MessageBubble.tsx
echo. > frontend\src\components\chat\ChatInput.tsx
echo. > frontend\src\components\agents\AgentDashboard.tsx
echo. > frontend\src\components\agents\AgentStatus.tsx
echo. > frontend\src\components\agents\AgentThoughtStream.tsx
echo. > frontend\src\components\diagnosis\HypothesisList.tsx
echo. > frontend\src\components\diagnosis\EvidenceLedger.tsx
echo. > frontend\src\components\diagnosis\ConfidenceChart.tsx
echo. > frontend\src\components\ui\SuggestionPills.tsx
echo. > frontend\src\components\ui\BiasAlert.tsx
echo. > frontend\src\components\ui\LoadingSpinner.tsx

REM Create service files
echo. > frontend\src\services\api.ts
echo. > frontend\src\services\agentOrchestrator.ts
echo. > frontend\src\services\websocket.ts

REM Create store files
echo. > frontend\src\store\useDiagnosticStore.ts
echo. > frontend\src\store\useAgentStore.ts

REM Create hook files
echo. > frontend\src\hooks\useAgentConnection.ts
echo. > frontend\src\hooks\useDiagnosticSession.ts

REM Create types and utils
echo. > frontend\src\types\index.ts
echo. > frontend\src\utils\formatters.ts

echo Frontend files created.

REM Create test files
echo. > tests\__init__.py
echo. > tests\test_agents.py
echo. > tests\test_cases.py

REM Create root files
echo. > .gitignore
echo. > README.md
echo. > docker-compose.yml

echo.
echo ========================================
echo Project structure created successfully!
echo Location: C:\projects\tcs project\curabot
echo ========================================
dir /s /b
pause
