// AdminController.java
package com.monprojet.series.controller;

import com.monprojet.series.dto.request.ChangerMotDePasseRequest;
import com.monprojet.series.dto.response.StatistiquesAdminResponse;
import com.monprojet.series.dto.response.UtilisateurResponse;
import com.monprojet.series.entity.StatutUtilisateur;
import com.monprojet.series.mapper.UtilisateurMapper;
import com.monprojet.series.service.UtilisateurService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/admin/utilisateurs")
@RequiredArgsConstructor
public class AdminController {

    private final UtilisateurService utilisateurService;

    // Sécurisé au niveau SecurityConfig : hasRole("ADMIN") sur /api/admin/**

    @GetMapping
    public List<UtilisateurResponse> listerTous(
            @RequestParam(required = false) StatutUtilisateur statut) {
        var utilisateurs = (statut == null)
                ? utilisateurService.listerTous()
                : utilisateurService.listerParStatut(statut);
        return utilisateurs.stream().map(UtilisateurMapper::toResponse).toList();
    }

    @GetMapping("/statistiques")
    public StatistiquesAdminResponse statistiques() {
        return utilisateurService.statistiques();
    }

    @PatchMapping("/{id}/approuver")
    public UtilisateurResponse approuver(@PathVariable Long id) {
        return UtilisateurMapper.toResponse(utilisateurService.approuver(id));
    }

    @PatchMapping("/{id}/refuser")
    public UtilisateurResponse refuser(@PathVariable Long id) {
        return UtilisateurMapper.toResponse(utilisateurService.refuser(id));
    }

    @PatchMapping("/{id}/promouvoir")
    public UtilisateurResponse promouvoir(@PathVariable Long id) {
        return UtilisateurMapper.toResponse(utilisateurService.promouvoir(id));
    }

    @PatchMapping("/{id}/retrograder")
    public UtilisateurResponse retrograder(@PathVariable Long id) {
        return UtilisateurMapper.toResponse(utilisateurService.retrograder(id));
    }

    @PatchMapping("/{id}/mot-de-passe")
    public ResponseEntity<Void> changerMotDePasse(
            @PathVariable Long id,
            @Valid @RequestBody ChangerMotDePasseRequest request) {
        utilisateurService.changerMotDePasse(id, request.nouveauMotDePasse());
        return ResponseEntity.noContent().build();
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> supprimer(@PathVariable Long id) {
        utilisateurService.supprimer(id);
        return ResponseEntity.noContent().build();
    }
}