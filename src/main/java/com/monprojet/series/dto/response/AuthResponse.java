// AuthResponse.java
package com.monprojet.series.dto.response;

public record AuthResponse(
        String token,
        Long utilisateurId,
        String pseudo,
        String role,
        String statut,
        String message
) {
}