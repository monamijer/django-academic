package com.monprojet.series.dto.response;

public record StatistiquesAdminResponse(
        long totalUtilisateurs,
        long enAttente,
        long approuves,
        long refuses,
        long admins
) {
}