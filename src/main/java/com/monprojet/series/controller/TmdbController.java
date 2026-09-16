// TmdbController.java
package com.monprojet.series.controller;

import com.monprojet.series.dto.response.*;
import com.monprojet.series.service.TmdbService;
import lombok.RequiredArgsConstructor;
import java.util.Map;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/tmdb")
@RequiredArgsConstructor
public class TmdbController {

    private final TmdbService tmdbService;

    // ---------- Découverte paginée ----------

    @GetMapping("/recherche")
    public PageResponse<TmdbSerieResponse> rechercher(
            @RequestParam String titre,
            @RequestParam(required = false) Integer annee,
            @RequestParam(required = false) String langue,
            @RequestParam(defaultValue = "1") int page) {
        return tmdbService.rechercherParTitre(titre, annee, langue, page);
    }

    @GetMapping("/populaires")
    public PageResponse<TmdbSerieResponse> populaires(
            @RequestParam(defaultValue = "1") int page) {
        return tmdbService.listerPopulaires(page);
    }

    @GetMapping("/tendances")
    public PageResponse<TmdbSerieResponse> tendances(
            @RequestParam(defaultValue = "1") int page) {
        return tmdbService.listerTendances(page);
    }

    @GetMapping("/mieux-notees")
    public PageResponse<TmdbSerieResponse> mieuxNotees(
            @RequestParam(defaultValue = "1") int page) {
        return tmdbService.listerMieuxNotees(page);
    }

    @GetMapping("/diffusees-bientot")
    public PageResponse<TmdbSerieResponse> diffuseesBientot(
            @RequestParam(defaultValue = "1") int page) {
        return tmdbService.listerDiffuseesBientot(page);
    }

    @GetMapping("/decouvrir")
    public PageResponse<TmdbSerieResponse> decouvrir(
            @RequestParam(required = false) Long genre,
            @RequestParam(required = false) Integer annee,
            @RequestParam(required = false) Double noteMin,
            @RequestParam(defaultValue = "1") int page) {
        return tmdbService.decouvrir(genre, annee, noteMin, page);
    }

    // ---------- Non paginé (petites listes) ----------

    @GetMapping("/genres")
    public List<GenreResponse> genres() {
        return tmdbService.listerGenres();
    }

    @GetMapping("/serie/{tmdbId}")
    public TmdbSerieResponse detailSerie(@PathVariable Long tmdbId) {
        return tmdbService.obtenirDetail(tmdbId);
    }

    @GetMapping("/serie/{tmdbId}/similaires")
    public List<TmdbSerieResponse> similaires(@PathVariable Long tmdbId) {
        return tmdbService.listerSimilaires(tmdbId);
    }

    @GetMapping("/serie/{tmdbId}/recommandations")
    public List<TmdbSerieResponse> recommandations(@PathVariable Long tmdbId) {
        return tmdbService.listerRecommandations(tmdbId);
    }

    @GetMapping("/serie/{tmdbId}/credits")
    public List<MembreCastingResponse> credits(@PathVariable Long tmdbId) {
        return tmdbService.listerCredits(tmdbId);
    }

    @GetMapping("/acteur/{acteurId}")
    public ActeurResponse acteur(@PathVariable Long acteurId) {
        return tmdbService.obtenirActeur(acteurId);
    }

    @GetMapping("/recherche-acteur")
    public List<ActeurResponse> rechercherActeur(@RequestParam String nom) {
        return tmdbService.rechercherActeur(nom);
    }

    @GetMapping("/acteur/{acteurId}/series")
    public List<TmdbSerieResponse> seriesActeur(@PathVariable Long acteurId) {
        return tmdbService.listerSeriesActeur(acteurId);
    }

    @GetMapping("/serie/{tmdbId}/fournisseurs")
    public Map<String, List<FournisseurResponse>> fournisseurs(@PathVariable Long tmdbId) {
        return tmdbService.listerFournisseurs(tmdbId);
    }
}