# ArtCloak Frontend

A TypeScript-based frontend for the ArtCloak image transformation service.

## Features

- Upload images via drag-and-drop or file selection
- Transform images to Studio Ghibli style using the ArtCloak API
- Download transformed images

## Setup

1. Install dependencies:
```
npm install
```

2. Build the TypeScript code:
```
npm run build
```

3. Start the development server:
```
npm start
```

## Development

- Use `npm run watch` to automatically compile TypeScript changes
- The backend API should be running at http://localhost:8000

## Technologies

- TypeScript
- Modern browser APIs (Fetch, File, FormData, etc.)
- CSS3 for styling

## Notes

- The prompt "re-create this image in the style of studio ghibli" is hard-coded
- Only supports JPEG and PNG image formats
- API endpoint is configured to http://localhost:8000/generate/