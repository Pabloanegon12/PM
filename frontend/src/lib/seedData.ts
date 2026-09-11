import type { Board } from "./types";

export const seedBoard: Board = {
  columns: [
    { id: "backlog", name: "Backlog", cardIds: ["card-1", "card-2"] },
    { id: "todo", name: "Por hacer", cardIds: ["card-3", "card-4"] },
    { id: "in-progress", name: "En curso", cardIds: ["card-5", "card-6"] },
    { id: "in-review", name: "En revisión", cardIds: ["card-7"] },
    { id: "done", name: "Hecho", cardIds: ["card-8", "card-9"] },
  ],
  cards: {
    "card-1": {
      id: "card-1",
      title: "Definir arquitectura del backend",
      details: "Evaluar si conviene una API REST o GraphQL y documentar la decisión.",
    },
    "card-2": {
      id: "card-2",
      title: "Investigar proveedores de hosting",
      details: "Comparar precios y facilidad de despliegue entre Vercel, Railway y Render.",
    },
    "card-3": {
      id: "card-3",
      title: "Diseñar esquema de base de datos",
      details: "Modelar las tablas principales y sus relaciones antes de escribir migraciones.",
    },
    "card-4": {
      id: "card-4",
      title: "Configurar entorno de desarrollo",
      details: "Documentar los pasos para que cualquier persona del equipo pueda arrancar el proyecto en local.",
    },
    "card-5": {
      id: "card-5",
      title: "Implementar autenticación de usuarios",
      details: "Añadir inicio de sesión con email y contraseña, con validación en el servidor.",
    },
    "card-6": {
      id: "card-6",
      title: "Maquetar página de inicio",
      details: "Traducir el diseño de Figma a componentes reutilizables.",
    },
    "card-7": {
      id: "card-7",
      title: "Revisar pull request de la API de pagos",
      details: "Comprobar el manejo de errores y que los importes se redondean correctamente.",
    },
    "card-8": {
      id: "card-8",
      title: "Configurar repositorio en GitHub",
      details: "Crear el repositorio, proteger la rama principal y añadir la plantilla de pull requests.",
    },
    "card-9": {
      id: "card-9",
      title: "Redactar documento de requisitos",
      details: "Recoger el alcance del MVP y compartirlo con el equipo para validarlo.",
    },
  },
};
