# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- `yarn dev` - Start local preview server at http://localhost:3000
- `yarn build` - Build the static site
- `yarn deploy` - Deploy to Observable
- `yarn backstoptest` - Run visual regression tests
- `yarn backstopref` - Update reference screenshots for tests
- `yarn clean` - Clear the local data loader cache

## Code Style Guidelines
- **Imports**: Use named imports for specific features and import from npm: prefix (e.g., `import { icon } from 'npm:@fortawesome/fontawesome-svg-core'`)
- **Documentation**: Use JSDoc comments for functions with parameter descriptions
- **Error Handling**: Use default values and validation for coordinates and other data
- **Naming**: Use camelCase for variables and functions, descriptive names
- **Libraries**: Leverage Lodash for collections manipulation with `_.` prefix
- **Formatting**: Use consistent indentation (2 spaces) and semicolons
- **Component Structure**: Keep related functions together, follow Observable Framework patterns