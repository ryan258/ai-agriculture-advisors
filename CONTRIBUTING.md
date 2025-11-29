# Contributing to AI Agriculture Advisors

Thank you for your interest in contributing to AI Agriculture Advisors! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Adding New Features](#adding-new-features)
- [Testing Guidelines](#testing-guidelines)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behaviors include:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards others

**Unacceptable behaviors include:**
- Harassment, trolling, or discriminatory comments
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

## Getting Started

### Prerequisites

- Node.js (v14 or later)
- npm
- Git
- Ollama with llama3.1:latest
- MongoDB (optional)
- A code editor (VS Code recommended)

### Development Setup

1. **Fork the repository**

   Click the "Fork" button on GitHub.

2. **Clone your fork**

   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-agriculture-advisors.git
   cd ai-agriculture-advisors
   ```

3. **Add upstream remote**

   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/ai-agriculture-advisors.git
   ```

4. **Install dependencies**

   ```bash
   npm install
   ```

5. **Configure environment**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. **Start Ollama**

   ```bash
   ollama serve
   ollama pull llama3.1:latest
   ```

7. **Run the application**

   ```bash
   npm run dev
   ```

## Development Workflow

### Staying Synchronized

Always sync with the upstream repository before starting new work:

```bash
git checkout main
git fetch upstream
git merge upstream/main
git push origin main
```

### Creating a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or fixes

### Making Changes

1. Write your code following our [Coding Standards](#coding-standards)
2. Test your changes locally
3. Commit with descriptive messages (see [Commit Messages](#commit-messages))
4. Push to your fork
5. Open a Pull Request

## Coding Standards

### General Principles

- **DRY (Don't Repeat Yourself)** - Avoid code duplication
- **KISS (Keep It Simple)** - Favor simplicity over complexity
- **YAGNI (You Aren't Gonna Need It)** - Don't add features "just in case"
- **Separation of Concerns** - Keep different functionalities isolated

### JavaScript Style Guide

#### Formatting

- **Indentation:** 4 spaces (not tabs)
- **Line length:** Max 100 characters
- **Semicolons:** Use them
- **Quotes:** Single quotes for strings (except JSON)
- **Trailing commas:** Use them in multi-line objects/arrays

#### Naming Conventions

```javascript
// Classes: PascalCase
class AgricultureExpert { }

// Functions/Methods: camelCase
function processQuery() { }

// Constants: UPPER_SNAKE_CASE
const API_URL = 'http://localhost:11434';

// Variables: camelCase
const expertRoles = [];

// Private properties: prefix with underscore
class Service {
    _privateMethod() { }
}
```

#### Code Structure

**Controllers** should follow this pattern:

```javascript
const llamaService = require('../services/llamaService');
const { logger } = require('../utils/logger');

class ExpertController {
    async processQuery(query) {
        try {
            const prompt = this._buildPrompt(query);
            const response = await llamaService.generateResponse(prompt);
            return this.processResponse(response);
        } catch (error) {
            logger.error(`Error in ${this.constructor.name}: ${error.message}`);
            throw new Error(`Failed to process query in ${this.constructor.name}`);
        }
    }

    _buildPrompt(query) {
        return `System prompt here...

        User Query: ${query}`;
    }

    processResponse(response) {
        return response.trim();
    }
}

module.exports = new ExpertController();
```

**Services** should:
- Be stateless when possible
- Support dependency injection
- Export both class and singleton instance

```javascript
class MyService {
    constructor(dependency) {
        this.dependency = dependency || defaultDependency;
    }

    async doSomething() {
        // Implementation
    }
}

module.exports = new MyService(); // Default instance
module.exports.MyService = MyService; // Class for DI
```

**Routes** should:
- Use middleware for validation
- Handle errors with try-catch
- Return consistent JSON responses

```javascript
router.post('/endpoint', validateMiddleware, async (req, res) => {
    try {
        const result = await service.process(req.body);
        res.json({ success: true, data: result });
    } catch (error) {
        // Let error handler middleware deal with it
        throw error;
    }
});
```

### Error Handling

Always use Winston logger, never `console.log` or `console.error`:

```javascript
const { logger } = require('../utils/logger');

// Good
logger.info('Server started');
logger.error(`Error: ${error.message}`);
logger.warn('Deprecated feature used');

// Bad
console.log('Server started');
console.error('Error:', error);
```

### Async/Await

- Always use async/await over callbacks or raw promises
- Always use try-catch with async functions
- Don't mix async/await with `.then()/.catch()`

```javascript
// Good
async function getData() {
    try {
        const data = await fetchData();
        return processData(data);
    } catch (error) {
        logger.error(`Failed to get data: ${error.message}`);
        throw error;
    }
}

// Bad
function getData() {
    return fetchData()
        .then(data => processData(data))
        .catch(error => console.error(error));
}
```

## Adding New Features

### Adding a New Expert

1. **Create the controller** (`src/controllers/yourExpert.js`):

```javascript
const llamaService = require('../services/llamaService');
const { logger } = require('../utils/logger');

class YourExpert {
    async processQuery(query) {
        try {
            const prompt = `You are a [Your Expert Role]. Your expertise includes...

            User Query: ${query}

            Provide detailed, practical advice...`;

            const response = await llamaService.generateResponse(prompt);
            return this.processResponse(response);
        } catch (error) {
            logger.error(`Error in YourExpert: ${error.message}`);
            throw new Error('Failed to process query in YourExpert');
        }
    }

    processResponse(response) {
        return response.trim();
    }
}

module.exports = new YourExpert();
```

2. **Register in experts config** (`src/config/experts.js`):

```javascript
const YourExpert = require('../controllers/yourExpert');

const expertMap = {
    // ... existing experts
    yourkey: { instance: YourExpert, label: 'Your Expert Title' }
};
```

3. **Update the UI** (`public/index.html`):

Add checkbox (around line 197):
```html
<label><input type="checkbox" name="expertRole" value="yourkey"> Your Expert Title</label><br>
```

Add to `getExpertLabel()` function (around line 320):
```javascript
case 'yourkey': return 'Your Expert Title';
```

4. **Update documentation:**
   - Add expert to README.md expert list
   - Update ROADMAP.md if this was a planned feature

5. **Test your expert:**
   - Test via UI
   - Test via API endpoint
   - Test in roundtable discussions

### Adding Middleware

Place in `src/middleware/`:

```javascript
const { logger } = require('../utils/logger');

const yourMiddleware = (req, res, next) => {
    try {
        // Validation/processing logic
        if (/* condition */) {
            return res.status(400).json({ message: 'Error message' });
        }
        next();
    } catch (error) {
        logger.error(`Middleware error: ${error.message}`);
        next(error); // Pass to error handler
    }
};

module.exports = yourMiddleware;
```

Register in `src/server.js`:
```javascript
const yourMiddleware = require('./middleware/yourMiddleware');
app.use(yourMiddleware);
```

### Adding New Routes

Create in `src/routes/`:

```javascript
const express = require('express');
const router = express.Router();
const { validateSomething } = require('../middleware/validateRequest');

router.post('/endpoint', validateSomething, async (req, res) => {
    try {
        // Implementation
        res.json({ success: true });
    } catch (error) {
        throw error; // Let error handler deal with it
    }
});

module.exports = router;
```

Register in `src/server.js`:
```javascript
const yourRoutes = require('./routes/yourRoutes');
app.use('/api/your-path', yourRoutes);
```

## Testing Guidelines

### Running Tests

```bash
npm test
```

*Note: Test infrastructure is coming soon. See ROADMAP.md*

### Test Structure (Future)

When writing tests:
- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Use Jest or Mocha (TBD)
- Aim for >80% code coverage

Example test structure:

```javascript
describe('AgricultureExpert', () => {
    describe('processQuery', () => {
        it('should return processed response', async () => {
            // Test implementation
        });

        it('should handle errors gracefully', async () => {
            // Test implementation
        });
    });
});
```

### Manual Testing Checklist

Before submitting PR:
- [ ] Application starts without errors
- [ ] Can query individual experts
- [ ] Multi-expert queries work
- [ ] Roundtable discussions work
- [ ] Error messages are user-friendly
- [ ] Logs are generated correctly
- [ ] No console.log statements in code
- [ ] Environment variables work as expected

## Commit Messages

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat:** New feature
- **fix:** Bug fix
- **docs:** Documentation changes
- **style:** Code formatting (not CSS)
- **refactor:** Code restructuring
- **test:** Adding/updating tests
- **chore:** Build process, dependencies

### Examples

**Good:**
```
feat(experts): add livestock management specialist

- Create LivestockSpecialist controller
- Register in experts config
- Add UI checkbox and label mapping
- Update documentation

Addresses #42
```

**Bad:**
```
update stuff
```

### Rules

- Use present tense ("add" not "added")
- Use imperative mood ("move" not "moves")
- First line max 72 characters
- Reference issues/PRs in footer
- Explain *what* and *why*, not *how*

## Pull Request Process

### Before Submitting

1. **Update from main:**
   ```bash
   git checkout main
   git pull upstream main
   git checkout your-branch
   git rebase main
   ```

2. **Self-review:**
   - Read through your changes
   - Check for debugging code
   - Verify no console.log statements
   - Ensure proper error handling

3. **Test thoroughly:**
   - Run manual tests
   - Check for breaking changes
   - Test edge cases

### PR Template

When opening a PR, include:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No console.log statements
- [ ] Changes generate no warnings
```

### Review Process

1. Maintainer reviews your PR
2. Address feedback with new commits
3. Once approved, your PR will be merged
4. Delete your branch after merge

### What Reviewers Look For

- Code quality and readability
- Proper error handling
- Consistent style
- No breaking changes (or properly documented)
- Tests (when available)
- Documentation updates

## Reporting Issues

### Before Creating an Issue

1. **Search existing issues** - Your issue might already be reported
2. **Check ROADMAP.md** - Feature might be planned
3. **Verify it's reproducible** - Provide clear steps

### Issue Template

**Bug Report:**
```markdown
## Description
Clear description of the bug

## Steps to Reproduce
1. Step one
2. Step two
3. See error

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS:
- Node version:
- npm version:
- LLM model:

## Logs
Relevant error logs
```

**Feature Request:**
```markdown
## Feature Description
Clear description of proposed feature

## Use Case
Why is this feature needed?

## Proposed Solution
How might this work?

## Alternatives Considered
Other approaches you've thought of
```

## Questions?

- **Documentation:** See [README.md](README.md)
- **Roadmap:** See [ROADMAP.md](ROADMAP.md)
- **Issues:** [GitHub Issues](https://github.com/yourusername/ai-agriculture-advisors/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/ai-agriculture-advisors/discussions)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to AI Agriculture Advisors! Your efforts help make sustainable agriculture more accessible worldwide. 🌾
