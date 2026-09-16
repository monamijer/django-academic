package com.monprojet.series.dto.response;

import java.time.LocalDateTime;

public record UtilisateurResponse(
        Long id,
        String pseudo,
        String email,
        String role,
        String statut,
        LocalDateTime dateInscription,
        LocalDateTime derniereConnexion
) {
}