// TmdbService.java
package com.monprojet.series.service;

import com.monprojet.series.dto.response.ActeurResponse;
import com.monprojet.series.dto.response.GenreResponse;
import com.monprojet.series.dto.response.MembreCastingResponse;
import com.monprojet.series.dto.response.PageResponse;
import com.monprojet.series.dto.response.TmdbSerieResponse;
import com.monprojet.series.dto.tmdb.*;
import com.monprojet.series.entity.Episode;
import com.monprojet.series.entity.Saison;
import com.monprojet.series.entity.Serie;
import com.monprojet.series.entity.Utilisateur;
import com.monprojet.series.exception.BusinessException;
import com.monprojet.series.exception.ResourceNotFoundException;
import com.monprojet.series.exception.TmdbIndisponibleException;
import com.monprojet.series.repository.EpisodeRepository;
import com.monprojet.series.repository.SaisonRepository;
import com.monprojet.series.repository.SerieRepository;
import com.monprojet.series.repository.UtilisateurRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestClientResponseException;
import org.springframework.web.util.UriBuilder;
import com.monprojet.series.dto.response.FournisseurResponse;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.Map;

import java.net.URI;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.function.Function;

@Service
@RequiredArgsConstructor
public class TmdbService {

    private final RestClient tmdbRestClient;
    private final SerieRepository serieRepository;
    private final SaisonRepository saisonRepository;
    private final EpisodeRepository episodeRepository;
    private final UtilisateurRepository utilisateurRepository;

    @Value("${tmdb.api.key}")
    private String apiKey;

    // ---------- Découverte paginée ----------

    public PageResponse<TmdbSerieResponse> rechercherParTitre(String titre, Integer annee, String langue, int page) {
        TmdbPageResponse reponse = appeler(uri -> {
            var b = uri.path("/search/tv")
                    .queryParam("api_key", apiKey)
                    .queryParam("language", langue != null ? langue : "fr-FR")
                    .queryParam("query", titre)
                    .queryParam("page", page);
            if (annee != null) b.queryParam("first_air_date_year", annee);
            return b.build();
        }, TmdbPageResponse.class);
        return versPage(reponse);
    }

    public PageResponse<TmdbSerieResponse> listerPopulaires(int page) {
        return listerPage("/tv/popular", page);
    }

    public PageResponse<TmdbSerieResponse> listerTendances(int page) {
        return listerPage("/trending/tv/week", page);
    }

    public PageResponse<TmdbSerieResponse> listerMieuxNotees(int page) {
        return listerPage("/tv/top_rated", page);
    }

    // TMDB has no direct "upcoming" concept for TV series (unlike movies);
    // "on_the_air" (currently airing new episodes) is the closest equivalent.
    public PageResponse<TmdbSerieResponse> listerDiffuseesBientot(int page) {
        return listerPage("/tv/on_the_air", page);
    }

    public PageResponse<TmdbSerieResponse> decouvrir(Long genreId, Integer annee, Double noteMin, int page) {
        TmdbPageResponse reponse = appeler(uri -> {
            var b = uri.path("/discover/tv")
                    .queryParam("api_key", apiKey)
                    .queryParam("language", "fr-FR")
                    .queryParam("page", page);
            if (genreId != null) b.queryParam("with_genres", genreId);
            if (annee != null) b.queryParam("first_air_date_year", annee);
            if (noteMin != null) b.queryParam("vote_average.gte", noteMin);
            return b.build();
        }, TmdbPageResponse.class);
        return versPage(reponse);
    }

    private PageResponse<TmdbSerieResponse> listerPage(String chemin, int page) {
        TmdbPageResponse reponse = appeler(uri -> uri.path(chemin)
                .queryParam("api_key", apiKey)
                .queryParam("language", "fr-FR")
                .queryParam("page", page)
                .build(), TmdbPageResponse.class);
        return versPage(reponse);
    }

    // ---------- Non paginé ----------

    public List<GenreResponse> listerGenres() {
        TmdbGenresWrapper wrapper = appeler(uri -> uri.path("/genre/tv/list")
                .queryParam("api_key", apiKey)
                .queryParam("language", "fr-FR")
                .build(), TmdbGenresWrapper.class);
        return wrapper.genres().stream().map(g -> new GenreResponse(g.id(), g.name())).toList();
    }

    public TmdbSerieResponse obtenirDetail(Long tmdbId) {
        TmdbSerieDetailDto detail = recupererDetail(tmdbId);
        return new TmdbSerieResponse(
                detail.id(), detail.name(), detail.overview(),
                detail.firstAirDate(), detail.voteAverage(), construireUrlImage(detail.posterPath())
        );
    }

    public List<TmdbSerieResponse> listerSimilaires(Long tmdbId) {
        TmdbPageResponse page = appeler(uri -> uri.path("/tv/{id}/similar")
                .queryParam("api_key", apiKey)
                .queryParam("language", "fr-FR")
                .build(tmdbId), TmdbPageResponse.class);
        return versReponses(page);
    }

    public List<TmdbSerieResponse> listerRecommandations(Long tmdbId) {
        TmdbPageResponse page = appeler(uri -> uri.path("/tv/{id}/recommendations")
                .queryParam("api_key", apiKey)
                .queryParam("language", "fr-FR")
                .build(tmdbId), TmdbPageResponse.class);
        return versReponses(page);
    }

    public List<MembreCastingResponse> listerCredits(Long tmdbId) {
        TmdbCreditsDto credits = appeler(uri -> uri.path("/tv/{id}/credits")
                .queryParam("api_key", apiKey)
                .queryParam("language", "fr-FR")
                .build(tmdbId), TmdbCreditsDto.class);

        return credits.cast().stream()
                .map(c -> new MembreCastingResponse(c.id(), c.name(), c.character(), construireUrlImage(c.profilePath())))
                .toList();
    }

        /** Watch providers. */
    public Map<String, List<FournisseurResponse>> listerFournisseurs(Long tmdbId) {
        TmdbWatchProvidersDto dto = appeler(uri -> uri.path("/tv/{id}/watch/providers")
                .queryParam("api_key", apiKey)
                .build(tmdbId), TmdbWatchProvidersDto.class);

        Map<String, List<FournisseurResponse>> resultat = new LinkedHashMap<>();

        if (dto.results() == null) return resultat;

        dto.results().forEach((codePays, data) -> {
            List<FournisseurResponse> liste = new ArrayList<>();

            ajouterFournisseurs(liste, data.flatrate(), "FLATRATE", data.link());
            ajouterFournisseurs(liste, data.rent(),     "RENT",     data.link());
            ajouterFournisseurs(liste, data.buy(),      "BUY",      data.link());

            if (!liste.isEmpty()) {
                resultat.put(codePays, liste);
            }
        });

        return resultat;
    }

    private void ajouterFournisseurs(List<FournisseurResponse> cible,
                                     List<TmdbWatchProvidersDto.Provider> sources,
                                     String type,
                                     String lien) {
        if (sources == null) return;
        sources.forEach(p -> cible.add(new FournisseurResponse(
                p.providerName(),
                construireUrlLogoProvider(p.logoPath()),
                type,
                lien
        )));
    }

    /** TMDB stock logos providers en /xxx.jpg  */
    private String construireUrlLogoProvider(String logoPath) {
        return logoPath == null ? null : "https://image.tmdb.org/t/p/w92" + logoPath;
    }

    // ---------- Acteurs ----------

    public List<ActeurResponse> rechercherActeur(String nom) {
        TmdbActeurPageResponse page = appeler(uri -> uri.path("/search/person")
                .queryParam("api_key", apiKey)
                .queryParam("language", "fr-FR")
                .queryParam("query", nom)
                .build(), TmdbActeurPageResponse.class);

        return page.results().stream()
                .map(a -> new ActeurResponse(a.id(), a.name(), null, null, null, construireUrlImage(a.profilePath())))
                .toList();
    }

    public ActeurResponse obtenirActeur(Long acteurId) {
        TmdbActeurDetailDto detail = appeler(uri -> uri.path("/person/{id}")
                .queryParam("api_key", apiKey)
                .queryParam("language", "fr-FR")
                .build(acteurId), TmdbActeurDetailDto.class);

        return new ActeurResponse(
                detail.id(), detail.name(), detail.biography(),
                detail.birthday(), detail.lieuNaissance(), construireUrlImage(detail.profilePath())
        );
    }

    public List<TmdbSerieResponse> listerSeriesActeur(Long acteurId) {
        TmdbActeurSeriesWrapper wrapper = appeler(uri -> uri.path("/person/{id}/tv_credits")
                .queryParam("api_key", apiKey)
                .queryParam("language", "fr-FR")
                .build(acteurId), TmdbActeurSeriesWrapper.class);

        return wrapper.cast().stream()
                .map(dto -> new TmdbSerieResponse(
                        dto.id(), dto.name(), dto.overview(),
                        dto.firstAirDate(), dto.voteAverage(), construireUrlImage(dto.posterPath())
                ))
                .toList();
    }

    // ---------- Import ----------

    @Transactional
    public Serie importerSerie(Long utilisateurId, Long tmdbId) {
        if (serieRepository.findByTmdbIdAndUtilisateurId(tmdbId, utilisateurId).isPresent()) {
            throw new BusinessException("Cette série TMDB a déjà été importée (tmdbId=" + tmdbId + ").");
        }

        Utilisateur utilisateur = utilisateurRepository.findById(utilisateurId)
                .orElseThrow(() -> new ResourceNotFoundException("Utilisateur introuvable : id=" + utilisateurId));

        TmdbSerieDetailDto detail = recupererDetail(tmdbId);

        Serie serie = Serie.builder()
                .titre(detail.name())
                .description(detail.overview())
                .anneeSortie(extraireAnnee(detail.firstAirDate()))
                .note(detail.voteAverage())
                .imageUrl(construireUrlImage(detail.posterPath()))
                .tmdbId(detail.id())
                .utilisateur(utilisateur)
                .build();
        serie = serieRepository.save(serie);

        for (TmdbSeasonDto saisonDto : detail.seasons()) {
            // TMDB season 0 ("Specials") is skipped to keep season numbering
            // aligned with what the rest of the app expects (RG2, RG3).
            if (saisonDto.numeroSaison() == 0) continue;
            importerSaison(serie, tmdbId, saisonDto);
        }

        return serie;
    }

    private void importerSaison(Serie serie, Long tmdbId, TmdbSeasonDto saisonDto) {
        Saison saison = Saison.builder()
                .numero(saisonDto.numeroSaison())
                .nbEpisodes(saisonDto.nombreEpisodes())
                .serie(serie)
                .build();
        saison = saisonRepository.save(saison);

        TmdbSeasonDetailDto saisonDetail = appeler(uri -> uri.path("/tv/{id}/season/{numero}")
                .queryParam("api_key", apiKey)
                .queryParam("language", "fr-FR")
                .build(tmdbId, saisonDto.numeroSaison()), TmdbSeasonDetailDto.class);

        Saison saisonFinale = saison;
        List<Episode> episodes = saisonDetail.episodes().stream()
                .map(ep -> Episode.builder()
                        .numero(ep.numeroEpisode())
                        .titre(ep.name())
                        .dureeMinutes(ep.runtime())
                        .saison(saisonFinale)
                        .build())
                .toList();
        episodeRepository.saveAll(episodes);
    }

    // ---------- Helpers ----------

    private TmdbSerieDetailDto recupererDetail(Long tmdbId) {
        return appeler(uri -> uri.path("/tv/{id}")
                .queryParam("api_key", apiKey)
                .queryParam("language", "fr-FR")
                .build(tmdbId), TmdbSerieDetailDto.class);
    }

    /** Convertit une réponse TMDB paginée en {@link PageResponse} pour le frontend. */
    private PageResponse<TmdbSerieResponse> versPage(TmdbPageResponse page) {
        return new PageResponse<>(
                versReponses(page),
                page.page(),
                page.totalPages(),
                page.totalResults()
        );
    }

    private List<TmdbSerieResponse> versReponses(TmdbPageResponse page) {
        return page.results().stream()
                .map(dto -> new TmdbSerieResponse(
                        dto.id(), dto.name(), dto.overview(),
                        dto.firstAirDate(), dto.voteAverage(), construireUrlImage(dto.posterPath())
                ))
                .toList();
    }

    private String construireUrlImage(String posterPath) {
        return posterPath == null ? null : "https://image.tmdb.org/t/p/w342" + posterPath;
    }

    private Integer extraireAnnee(String firstAirDate) {
        if (firstAirDate == null || firstAirDate.length() < 4) return null;
        return Integer.parseInt(firstAirDate.substring(0, 4));
    }

    // Single choke point for every TMDB call: any HTTP/network failure becomes
    // ResourceNotFoundException (404 from TMDB) or TmdbIndisponibleException
    // (everything else), so callers never touch RestClient error handling directly.
    private <T> T appeler(Function<UriBuilder, URI> uriFn, Class<T> type) {
        try {
            return tmdbRestClient.get().uri(uriFn::apply).retrieve().body(type);
        } catch (RestClientResponseException ex) {
            if (ex.getStatusCode().value() == 404) {
                throw new ResourceNotFoundException("Ressource TMDB introuvable.");
            }
            throw new TmdbIndisponibleException("TMDB a renvoyé une erreur (" + ex.getStatusCode() + ").", ex);
        } catch (RestClientException ex) {
            throw new TmdbIndisponibleException("Impossible de contacter TMDB.", ex);
        }
    }
}