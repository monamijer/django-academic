package com.monprojet.series.dto.response;

/**
 * 
 *
 * @param nom       name of the Provider (ex: "Netflix")
 * @param logoUrl   URL or logo (or null)
 * @param type      FLATRATE (subscribe), RENT (location), BUY
 * @param lien      link TMDB "watch" for this country (eg: https://www.themoviedb.org/...)
 */
public record FournisseurResponse(
        String nom,
        String logoUrl,
        String type,
        String lien
) {
}