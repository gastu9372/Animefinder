# Ticket: TICKET-008 - Frontend User Interface & Interactive Result Experience

* **ID:** TICKET-008
* **Título:** Interfaz React Completa de Búsqueda por Imagen y Descripción con Feedback Visual de Resultados
* **Rama asignada:** `feature/result-ui`
* **Asignado a:** Frontend Developer
* **Revisor / QA:** QA & Security Tester
* **Estado:** done
* **Dependencias:** TICKET-002 (Frontend Scaffold), TICKET-006 (Image Search), TICKET-007 (Text Search)


---

## 1. Objetivo
Construir una experiencia visual moderna, accesible y fluida para AnimeFinder en React 18 + TypeScript + Vanilla CSS. Debe permitir la búsqueda por imagen (drag & drop, selector de archivos y pegado desde portapapeles `Ctrl+V`), y por descripción en texto libre (con atajos de teclado, sugerencias de prueba y contador de caracteres). Los resultados deben presentarse en tarjetas interactivas con portadas en alta resolución, indicador de confianza/similitud coloreado, badges de episodio/timestamp, reproductor de vista previa de escena, explicación del razonamiento de Gemini ("match_reason"), filtro/blur para contenido adulto y manejo integral de estados (carga con skeletons, errores RFC 7807 con reintento, y estados vacíos).

---

## 2. Criterios de Aceptación Técnicos
1. **Componentes de Búsqueda:**
   - **Tabs / Selector de Modo:** Alternar entre "Búsqueda por Imagen" y "Búsqueda por Descripción" con transiciones suaves y foco accesible.
   - **ImageDropzone (`src/components/ImageDropzone.tsx`):**
     - Soporta Drag & Drop, selección por click y pegado de capturas con `Ctrl+V` (evento `paste` global en ventana).
     - Validación del lado del cliente: tipos de archivo (JPEG, PNG, WebP) y tamaño máximo de 8 MB.
     - Vista previa interactiva de la imagen seleccionada con opción de remover/reemplazar.
   - **TextSearchForm (`src/components/TextSearchForm.tsx`):**
     - Textarea accesible con límite de 500 caracteres y contador visual en tiempo real.
     - Atajo de teclado: `Enter` o `Ctrl+Enter` para enviar la búsqueda.
     - Chips de sugerencias interactivas para probar rápidamente búsquedas comunes.
2. **Visualización de Resultados (`src/components/ResultCard.tsx` y `ResultList.tsx`):**
   - **Jerarquía de Títulos:** Título canónico en Romaji destacado, con títulos en Inglés y Kanji nativo en jerarquía secundaria.
   - **Indicador de Confianza:**
     - En búsqueda por imagen: porcentaje numérico (`98.5%`) y badge de color (Verde/Alta >= 85%, Amarillo/Media >= 70%, Rojo/Baja < 70%).
     - En búsqueda por texto: badge de nivel de confianza (`high`, `medium`, `low`) y caja estilizada con la justificación de IA (`match_reason`).
   - **Información de Escena:** Si `scene_info` está presente, mostrar badges de Episodio, Timestamp formateado (`MM:SS`) y botón para reproducir el clip de video de vista previa si está disponible.
   - **Etiquetas de Metadatos:** Año de estreno, formato (TV, Película, OVA, etc.), y badges de motor ("Motor: Gemini IA" o "Modo Fallback: AniList").
   - **Protección de Contenido Adulto (+18):** Si `is_adult` es verdadero, mostrar advertencia con blur visual y botón toggle "Mostrar contenido sensible".
   - **Badge de Rendimiento y Caché:** Indicar tiempo de respuesta en ms y si el resultado provino de caché.
3. **Manejo de Estados de UI (`src/components/SkeletonLoader.tsx`, `ErrorAlert.tsx`, `EmptyState.tsx`):**
   - **Skeleton Loader:** Animación shimmer mientras la petición está en progreso.
   - **Error Alert:** Parseo y renderizado amigable de errores RFC 7807 (ej: límite de peticiones con temporizador de reintento).
   - **Empty State:** Mensaje orientativo cuando no se encuentren coincidencias.
4. **Testing de Componentes:**
   - Pruebas unitarias con Vitest y `@testing-library/react` para validar renderizado de tarjetas, dropzone y alternancia de modos.

---

## 3. Archivos Involucrados
- `frontend/src/components/ImageDropzone.tsx`
- `frontend/src/components/TextSearchForm.tsx`
- `frontend/src/components/ResultCard.tsx`
- `frontend/src/components/ResultList.tsx`
- `frontend/src/components/SkeletonLoader.tsx`
- `frontend/src/components/ErrorAlert.tsx`
- `frontend/src/components/EmptyState.tsx`
- `frontend/src/styles/components.css`
- `frontend/src/App.tsx`
- `frontend/src/services/apiClient.ts`
- `frontend/tests/components.test.tsx`
- `docs/tickets/TICKET-008-result-ui.md`
