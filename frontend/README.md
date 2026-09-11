# Curso Claude

MVP de un tablero Kanban de un solo tablero, con 5 columnas fijas renombrables y tarjetas con título y detalles. Sin persistencia ni gestión de usuarios: el estado vive en memoria y se reinicia con datos de ejemplo en cada recarga.

## Desarrollo

```bash
npm install
npm run dev
```

Abre [http://localhost:3000](http://localhost:3000).

## Pruebas

```bash
npm run test      # unitarios (Vitest)
npm run test:e2e  # integración (Playwright)
```

## Stack

Next.js (App Router, TypeScript), Tailwind CSS, dnd-kit para arrastrar y soltar.
