// UtilisateurMapper.java
package com.monprojet.series.mapper;

import com.monprojet.series.dto.request.UtilisateurRequest;
import com.monprojet.series.dto.response.UtilisateurResponse;
import com.monprojet.series.entity.Utilisateur;

public final class UtilisateurMapper {

    private UtilisateurMapper() {}

    public static Utilisateur toEntity(UtilisateurRequest request) {
        return Utilisateur.builder()
                .pseudo(request.pseudo())
                .email(request.email())
                .build();
    }

    public static UtilisateurResponse toResponse(Utilisateur utilisateur) {
        return new UtilisateurResponse(
                utilisateur.getId(),
                utilisateur.getPseudo(),
                utilisateur.getEmail(),
                utilisateur.getRole().name(),
                utilisateur.getStatut().name(),
                utilisateur.getDateInscription(),
                utilisateur.getDerniereConnexion()
        );
    }
}