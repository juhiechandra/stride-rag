# Stride RAG Frontend

The frontend for the Stride RAG multimodal Retrieval Augmented Generation system.

## Overview

This React-based frontend provides a user interface for interacting with the Stride RAG system. It allows users to:

- Upload and manage documents
- Chat with AI models about document content
- View and analyze document information
- Configure system settings

## Technology Stack

- **React**: UI library
- **React Router**: For navigation
- **Styled Components**: For styling
- **Mantine**: UI component library
- **Vite**: Build tool and development server

## Project Structure

```
frontend/
├── public/             # Static assets
├── src/                # Source code
│   ├── assets/         # Images and other assets
│   ├── components/     # Reusable UI components
│   │   ├── Layout/     # Layout components
│   │   └── styled/     # Styled components
│   ├── pages/          # Page components
│   ├── styles/         # CSS and styling
│   ├── utils/          # Utility functions
│   ├── App.jsx         # Main application component
│   └── main.jsx        # Entry point
├── package.json        # Node.js dependencies
└── vite.config.js      # Vite configuration
```

## Setup and Installation

1. Make sure you have Node.js 16+ installed
2. Install dependencies:

   ```bash
   npm install
   ```

3. Start the development server:

   ```bash
   npm run dev
   ```

4. Access the application at `http://localhost:5173`

## Available Scripts

- `npm run dev`: Start the development server
- `npm run build`: Build the production version
- `npm run lint`: Run ESLint to check code quality
- `npm run preview`: Preview the production build locally

## Connecting to the Backend

The frontend is configured to connect to the backend API running at `http://localhost:8000`. If your backend is running on a different URL, you'll need to update the API endpoint URLs in the code.

## Authentication

The application includes a simple authentication system. The default login credentials are:

- **Username**: admin
- **Password**: password

In a production environment, you should implement proper authentication with JWT or OAuth.

## Contributing

When contributing to the frontend, please follow these guidelines:

1. Use functional components with hooks
2. Follow the existing styling patterns
3. Keep components small and focused
4. Add proper documentation for new components
5. Test your changes thoroughly before submitting
