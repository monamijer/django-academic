// TmdbWatchProvidersDto.java — mirrors TMDB /tv/{id}/watch/providers payload
package com.monprojet.series.dto.tmdb;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;
import java.util.Map;

@JsonIgnoreProperties(ignoreUnknown = true)
public record TmdbWatchProvidersDto(
        Map<String, PaysProviders> results
) {
    @JsonIgnoreProperties(ignoreUnknown = true)
    public record PaysProviders(
            String link,
            List<Provider> flatrate,
            List<Provider> rent,
            List<Provider> buy
    ) {}

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record Provider(
            @JsonProperty("provider_id") int providerId,
            @JsonProperty("provider_name") String providerName,
            @JsonProperty("logo_path") String logoPath,
            @JsonProperty("display_priority") int displayPriority
    ) {}
}