import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import App from '../src/App';

describe('App Component', () => {
  it('renderiza el título principal de AnimeFinder y opciones de búsqueda', () => {
    render(<App />);

    const brandTitles = screen.getAllByText(/Anime/i);
    expect(brandTitles.length).toBeGreaterThan(0);

    const imageButtons = screen.getAllByText(/Por Imagen/i);
    expect(imageButtons.length).toBeGreaterThan(0);

    const descButtons = screen.getAllByText(/Por Descripción/i);
    expect(descButtons.length).toBeGreaterThan(0);
  });


  it('renderiza la atribución formal a trace.moe y AniList en el pie de página', () => {
    render(<App />);

    const traceLink = screen.getByRole('link', { name: /trace\.moe/i });
    expect(traceLink).toBeInTheDocument();
    expect(traceLink).toHaveAttribute('href', 'https://trace.moe');

    const anilistLink = screen.getByRole('link', { name: /AniList GraphQL API/i });
    expect(anilistLink).toBeInTheDocument();
    expect(anilistLink).toHaveAttribute('href', 'https://anilist.co');
  });
});
